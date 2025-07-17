from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Conversation, Message, ChatbotSession
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    MessageSerializer,
    SendMessageSerializer,
    StartConversationSerializer,
    ConversationUpdateSerializer,
    SessionFeedbackSerializer,
    ConversationStatsSerializer,
    UserChatHistorySerializer
)
from .dummy_ai_service import dummy_medical_chatbot
from skin_analysis.models import SkinAnalysis


class StartConversationView(APIView):
    """Start a new conversation with the chatbot"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start new conversation with initial message"""
        serializer = StartConversationSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            initial_message = serializer.validated_data['initial_message']
            title = serializer.validated_data.get('title', '')
            analysis_id = serializer.validated_data.get('analysis_id')

            # Get related analysis if provided
            related_analysis = None
            if analysis_id:
                try:
                    related_analysis = SkinAnalysis.objects.get(id=analysis_id, user=user)
                except SkinAnalysis.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Analysis not found or access denied'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Create conversation
            conversation = Conversation.objects.create(
                user=user,
                title=title or f"Chat started {timezone.now().strftime('%B %d, %Y')}",
                related_analysis=related_analysis
            )

            # Create user message
            user_message = Message.objects.create(
                conversation=conversation,
                message_type='user',
                content=initial_message
            )

            # Prepare context for AI
            user_context = self._get_user_context(user, related_analysis)

            # Generate AI response
            try:
                ai_response = dummy_medical_chatbot.generate_response(
                    initial_message,
                    user_context
                )

                if ai_response.get('status') == 'success':
                    # Create assistant message
                    assistant_message = Message.objects.create(
                        conversation=conversation,
                        message_type='assistant',
                        content=ai_response['response'],
                        response_time=ai_response.get('response_time'),
                        confidence_score=ai_response.get('confidence_score'),
                        user_context=user_context
                    )

                    # Update conversation timestamp
                    conversation.last_message_at = timezone.now()
                    conversation.save()

                    # Create session tracking
                    ChatbotSession.objects.create(
                        user=user,
                        conversation=conversation,
                        total_messages=2
                    )

                    # Serialize conversation with messages
                    conversation_serializer = ConversationSerializer(
                        conversation,
                        context={'request': request}
                    )

                    return Response({
                        'success': True,
                        'message': 'Conversation started successfully',
                        'conversation': conversation_serializer.data,
                        'ai_suggestions': ai_response.get('suggestions', [])
                    }, status=status.HTTP_201_CREATED)

                else:
                    # AI service error
                    return Response({
                        'success': False,
                        'error': 'Failed to generate AI response'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def _get_user_context(self, user, related_analysis=None):
        """Get user context for AI response generation"""
        context = {
            'user_id': str(user.id),
            'analysis_count': user.analysis_count,
            'member_since': user.created_at.strftime('%B %Y')
        }

        if related_analysis:
            context['recent_analysis'] = {
                'predicted_disease': related_analysis.predicted_disease,
                'confidence_percentage': related_analysis.confidence_percentage,
                'analysis_date': related_analysis.analysis_date.isoformat()
            }

        return context


class SendMessageView(APIView):
    """Send a message in existing conversation"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Send message to existing conversation"""
        serializer = SendMessageSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            content = serializer.validated_data['content']
            conversation_id = serializer.validated_data.get('conversation_id')

            # Get or create conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=user)
                except Conversation.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Conversation not found or access denied'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': False,
                    'error': 'Conversation ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if conversation is active
            if not conversation.is_active:
                return Response({
                    'success': False,
                    'error': 'Cannot send message to inactive conversation'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user message
            user_message = Message.objects.create(
                conversation=conversation,
                message_type='user',
                content=content
            )

            # Get conversation history for context
            previous_messages = Message.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:10]

            message_history = [
                {
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in reversed(previous_messages)
            ]

            # Prepare context for AI
            user_context = self._get_user_context(user, conversation.related_analysis)
            user_context['conversation_history'] = message_history

            # Generate AI response
            try:
                ai_response = dummy_medical_chatbot.generate_response(
                    content,
                    user_context
                )

                if ai_response.get('status') == 'success':
                    # Create assistant message
                    assistant_message = Message.objects.create(
                        conversation=conversation,
                        message_type='assistant',
                        content=ai_response['response'],
                        response_time=ai_response.get('response_time'),
                        confidence_score=ai_response.get('confidence_score'),
                        user_context=user_context
                    )

                    # Update conversation timestamp
                    conversation.last_message_at = timezone.now()
                    conversation.save()

                    # Update session statistics
                    session = ChatbotSession.objects.filter(
                        conversation=conversation
                    ).order_by('-session_start').first()

                    if session:
                        session.total_messages += 2
                        session.save()

                    # Serialize messages
                    user_msg_serializer = MessageSerializer(user_message)
                    assistant_msg_serializer = MessageSerializer(assistant_message)

                    return Response({
                        'success': True,
                        'message': 'Message sent successfully',
                        'user_message': user_msg_serializer.data,
                        'assistant_message': assistant_msg_serializer.data,
                        'ai_suggestions': ai_response.get('suggestions', []),
                        'conversation_id': str(conversation.id)
                    }, status=status.HTTP_200_OK)

                else:
                    return Response({
                        'success': False,
                        'error': 'Failed to generate AI response'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def _get_user_context(self, user, related_analysis=None):
        """Get user context for AI response generation"""
        context = {
            'user_id': str(user.id),
            'analysis_count': user.analysis_count,
            'member_since': user.created_at.strftime('%B %Y')
        }

        if related_analysis:
            context['recent_analysis'] = {
                'predicted_disease': related_analysis.predicted_disease,
                'confidence_percentage': related_analysis.confidence_percentage,
                'analysis_date': related_analysis.analysis_date.isoformat()
            }

        return context


class ConversationListView(APIView):
    """Get list of user's conversations"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's conversation list with pagination"""
        user = request.user

        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        is_active = request.GET.get('is_active')

        # Calculate offset
        offset = (page - 1) * limit

        # Base queryset
        conversations = Conversation.objects.filter(user=user).order_by('-last_message_at')

        # Apply filters
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            conversations = conversations.filter(is_active=is_active_bool)

        # Get total count
        total_count = conversations.count()

        # Get paginated results
        paginated_conversations = conversations[offset:offset + limit]

        # Serialize conversations
        serializer = ConversationListSerializer(
            paginated_conversations,
            many=True,
            context={'request': request}
        )

        return Response({
            'success': True,
            'data': {
                'conversations': serializer.data,
                'pagination': {
                    'current_page': page,
                    'total_pages': (total_count + limit - 1) // limit,
                    'total_count': total_count,
                    'has_next': offset + limit < total_count,
                    'has_previous': page > 1
                }
            }
        }, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """Get, update, or delete specific conversation"""
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        """Get conversation details with messages"""
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            serializer = ConversationSerializer(conversation, context={'request': request})

            return Response({
                'success': True,
                'conversation': serializer.data
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, conversation_id):
        """Update conversation (title, active status)"""
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            serializer = ConversationUpdateSerializer(
                conversation,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()

                # Return updated conversation
                conversation_serializer = ConversationSerializer(
                    conversation,
                    context={'request': request}
                )

                return Response({
                    'success': True,
                    'message': 'Conversation updated successfully',
                    'conversation': conversation_serializer.data
                }, status=status.HTTP_200_OK)

            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, conversation_id):
        """Delete conversation and all messages"""
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation_title = conversation.title or str(conversation.id)
            conversation.delete()

            return Response({
                'success': True,
                'message': f'Conversation "{conversation_title}" deleted successfully'
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)


class ChatbotStatsView(APIView):
    """Get user's chatbot usage statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's chatbot statistics"""
        user = request.user

        # Basic stats
        total_conversations = Conversation.objects.filter(user=user).count()
        active_conversations = Conversation.objects.filter(user=user, is_active=True).count()
        total_messages = Message.objects.filter(conversation__user=user).count()

        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_conversations = Conversation.objects.filter(
            user=user,
            created_at__gte=thirty_days_ago
        ).count()

        recent_messages = Message.objects.filter(
            conversation__user=user,
            created_at__gte=thirty_days_ago
        ).count()

        # Average response time
        avg_response_time = Message.objects.filter(
            conversation__user=user,
            message_type='assistant',
            response_time__isnull=False
        ).aggregate(avg_time=Avg('response_time'))['avg_time']

        # Most active day
        most_recent_conversation = Conversation.objects.filter(user=user).order_by('-created_at').first()

        return Response({
            'success': True,
            'statistics': {
                'total_conversations': total_conversations,
                'active_conversations': active_conversations,
                'total_messages': total_messages,
                'recent_conversations_30_days': recent_conversations,
                'recent_messages_30_days': recent_messages,
                'average_response_time_seconds': round(avg_response_time, 2) if avg_response_time else 0,
                'most_recent_conversation': most_recent_conversation.last_message_at.isoformat() if most_recent_conversation else None,
                'member_since': user.created_at.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)


class SessionFeedbackView(APIView):
    """Submit feedback for chatbot session"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Submit session feedback"""
        serializer = SessionFeedbackSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            conversation_id = serializer.validated_data['conversation_id']
            satisfaction_rating = serializer.validated_data['satisfaction_rating']
            feedback_comment = serializer.validated_data.get('feedback_comment', '')

            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)

                # Get or create session
                session, created = ChatbotSession.objects.get_or_create(
                    user=user,
                    conversation=conversation,
                    defaults={
                        'total_messages': conversation.message_count,
                        'session_end': timezone.now()
                    }
                )

                # Update feedback
                session.satisfaction_rating = satisfaction_rating
                session.feedback_comment = feedback_comment
                if not session.session_end:
                    session.session_end = timezone.now()
                session.save()

                return Response({
                    'success': True,
                    'message': 'Feedback submitted successfully'
                }, status=status.HTTP_200_OK)

            except Conversation.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Conversation not found or access denied'
                }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SystemStatusView(APIView):
    """Get chatbot system status (public endpoint)"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Get chatbot system status"""
        return Response({
            'success': True,
            'status': 'operational',
            'chatbot_model': 'dummy_medical_chatbot_v1.0',
            'supported_topics': [
                'Skin conditions (acne, eczema, psoriasis, rosacea)',
                'General skincare advice',
                'Product recommendations',
                'Skincare routines'
            ],
            'features': [
                'Contextual responses based on skin analysis',
                'Medical disclaimers for safety',
                'Conversation history tracking',
                'Session feedback system'
            ],
            'authentication_required': True,
            'max_message_length': 2000,
            'average_response_time_seconds': 2.5,
            'version': '1.0.0',
            'endpoints': {
                'start_chat': '/api/v1/chatbot/start-chat/',
                'send_message': '/api/v1/chatbot/send-message/',
                'conversations': '/api/v1/chatbot/conversations/',
                'stats': '/api/v1/chatbot/stats/'
            }
        }, status=status.HTTP_200_OK)