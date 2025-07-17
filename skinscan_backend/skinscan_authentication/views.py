from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import login, logout
from django.db.models import Count, Q, Avg
from django.db import models
from datetime import datetime, timedelta

from .models import User, UserProfile
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    UserAnalysisHistorySerializer
)
from skin_analysis.models import SkinAnalysis
from skin_analysis.serializers import SkinAnalysisSerializer


class UserRegistrationView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Update last login
            user.last_login = datetime.now()
            user.save(update_fields=['last_login'])

            return Response({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'is_email_verified': user.is_email_verified,
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Get user profile information"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)


class UserProfileUpdateView(APIView):
    """Update user profile"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()

            # Return updated profile
            profile_serializer = UserProfileSerializer(request.user, context={'request': request})
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': profile_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserAnalysisHistoryView(APIView):
    """Get user's analysis history with detailed information"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        disease_filter = request.GET.get('disease', None)

        # Calculate offset
        offset = (page - 1) * limit

        # Base queryset
        analyses = SkinAnalysis.objects.filter(user=user).order_by('-analysis_date')

        # Apply disease filter if provided
        if disease_filter:
            analyses = analyses.filter(predicted_disease__icontains=disease_filter)

        # Get total count
        total_count = analyses.count()

        # Get paginated results
        paginated_analyses = analyses[offset:offset + limit]

        # Serialize analyses
        analyses_serializer = SkinAnalysisSerializer(
            paginated_analyses,
            many=True,
            context={'request': request}
        )

        # Get analysis statistics
        stats = self._get_analysis_statistics(user)

        return Response({
            'success': True,
            'data': {
                'analyses': analyses_serializer.data,
                'pagination': {
                    'current_page': page,
                    'total_pages': (total_count + limit - 1) // limit,
                    'total_count': total_count,
                    'has_next': offset + limit < total_count,
                    'has_previous': page > 1
                },
                'statistics': stats
            }
        }, status=status.HTTP_200_OK)

    def _get_analysis_statistics(self, user):
        """Get user's analysis statistics"""
        total_analyses = SkinAnalysis.objects.filter(user=user).count()

        # Get analyses from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_analyses = SkinAnalysis.objects.filter(
            user=user,
            analysis_date__gte=thirty_days_ago
        ).count()

        # Get most common conditions
        common_conditions = SkinAnalysis.objects.filter(user=user) \
                                .values('predicted_disease') \
                                .annotate(count=Count('predicted_disease')) \
                                .order_by('-count')[:5]

        # Average confidence score
        avg_confidence = SkinAnalysis.objects.filter(user=user) \
            .aggregate(avg_confidence=models.Avg('confidence_score'))['avg_confidence']

        return {
            'total_analyses': total_analyses,
            'recent_analyses_30_days': recent_analyses,
            'most_common_conditions': [
                {
                    'disease': item['predicted_disease'],
                    'count': item['count']
                } for item in common_conditions
            ],
            'average_confidence': round(avg_confidence * 100, 2) if avg_confidence else 0
        }


class UserDashboardView(APIView):
    """User dashboard with overview information"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get recent analyses (last 5)
        recent_analyses = SkinAnalysis.objects.filter(user=user) \
                              .order_by('-analysis_date')[:5]

        recent_analyses_serializer = SkinAnalysisSerializer(
            recent_analyses,
            many=True,
            context={'request': request}
        )

        # Get user statistics
        stats = self._get_dashboard_statistics(user)

        # Get user profile
        profile_serializer = UserProfileSerializer(user, context={'request': request})

        # Get chatbot statistics
        chatbot_stats = self._get_chatbot_statistics(user)

        return Response({
            'success': True,
            'dashboard': {
                'user_profile': profile_serializer.data,
                'recent_analyses': recent_analyses_serializer.data,
                'statistics': stats,
                'chatbot_statistics': chatbot_stats,
                'quick_actions': [
                    {
                        'title': 'New Analysis',
                        'description': 'Upload a new skin image for analysis',
                        'action': 'upload_image'
                    },
                    {
                        'title': 'Start Chat',
                        'description': 'Get AI-powered skin health consultation',
                        'action': 'start_chat'
                    },
                    {
                        'title': 'View History',
                        'description': 'Browse your previous analyses',
                        'action': 'view_history'
                    },
                    {
                        'title': 'Chat History',
                        'description': 'View your consultation conversations',
                        'action': 'view_chat_history'
                    },
                    {
                        'title': 'Update Profile',
                        'description': 'Update your profile information',
                        'action': 'update_profile'
                    }
                ]
            }
        }, status=status.HTTP_200_OK)

    def _get_dashboard_statistics(self, user):
        """Get dashboard statistics for user"""
        from django.db.models import Avg, Count

        total_analyses = SkinAnalysis.objects.filter(user=user).count()

        # Get this week's analyses
        week_ago = datetime.now() - timedelta(days=7)
        this_week_analyses = SkinAnalysis.objects.filter(
            user=user,
            analysis_date__gte=week_ago
        ).count()

        # Get this month's analyses
        month_ago = datetime.now() - timedelta(days=30)
        this_month_analyses = SkinAnalysis.objects.filter(
            user=user,
            analysis_date__gte=month_ago
        ).count()

        return {
            'total_analyses': total_analyses,
            'this_week': this_week_analyses,
            'this_month': this_month_analyses,
            'member_since': user.created_at.strftime('%B %Y')
        }

    def _get_chatbot_statistics(self, user):
        """Get chatbot statistics for dashboard"""
        try:
            from skinscan_chatbot.models import Conversation, Message

            total_conversations = Conversation.objects.filter(user=user).count()
            total_messages = Message.objects.filter(conversation__user=user, message_type='user').count()

            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_conversations = Conversation.objects.filter(
                user=user,
                created_at__gte=week_ago
            ).count()

            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'recent_conversations': recent_conversations
            }
        except ImportError:
            # Chatbot module not available
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'recent_conversations': 0
            }


class DeleteAccountView(APIView):
    """Delete user account"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        # Get password confirmation
        password = request.data.get('password')
        if not password or not user.check_password(password):
            return Response({
                'success': False,
                'error': 'Password confirmation required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete user (this will cascade to related objects)
        user_email = user.email
        user.delete()

        return Response({
            'success': True,
            'message': f'Account {user_email} has been permanently deleted'
        }, status=status.HTTP_200_OK)