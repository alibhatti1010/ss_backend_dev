from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import tempfile
import uuid
from PIL import Image

from .models import SkinAnalysis
from .serializers import SkinAnalysisSerializer, ImageUploadSerializer
from .dummy_ai_service import dummy_predictor


class ImageAnalysisView(APIView):
    """
    Handle image upload and analysis
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]  # Now requires authentication

    def post(self, request):
        """Upload image and get AI analysis"""

        try:
            # Validate input
            serializer = ImageUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            image_file = serializer.validated_data['image']

            # Save image temporarily for processing
            temp_path = self._save_temp_image(image_file)

            try:
                # Get AI prediction using dummy service
                prediction_result = dummy_predictor.predict(temp_path)

                if prediction_result.get('status') == 'error':
                    return Response({
                        'success': False,
                        'error': prediction_result.get('error', 'Analysis failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Save analysis to database with authenticated user
                analysis = self._save_analysis(image_file, prediction_result, request.user)

                # Prepare response
                response_data = {
                    'success': True,
                    'analysis_id': str(analysis.id),
                    'predicted_disease': analysis.predicted_disease,
                    'confidence_score': analysis.confidence_score,
                    'confidence_percentage': analysis.confidence_percentage,
                    'processing_time': round(analysis.processing_time, 2),
                    'analysis_date': analysis.analysis_date.isoformat(),
                    'image_info': {
                        'size': analysis.image_size,
                        'file_size_kb': round(analysis.file_size / 1024, 2) if analysis.file_size else 0
                    },
                    'message': 'Image analyzed successfully',
                    'disclaimer': 'This is a preliminary analysis for educational purposes only. Please consult a dermatologist for proper medical diagnosis.',
                    'user_info': {
                        'analysis_count': request.user.analysis_count,
                        'user_id': str(request.user.id)
                    }
                }

                return Response(response_data, status=status.HTTP_200_OK)

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _save_temp_image(self, image_file):
        """Save uploaded image to temporary file for processing"""
        # Create temp file with proper extension
        file_extension = os.path.splitext(image_file.name)[1].lower()
        if not file_extension:
            file_extension = '.jpg'

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            return temp_file.name

    def _save_analysis(self, image_file, prediction_result, user):
        """Save analysis results to database"""

        # Get image info
        image_info = prediction_result.get('image_info', {})

        analysis = SkinAnalysis.objects.create(
            user=user,  # Now always has authenticated user
            image=image_file,
            predicted_disease=prediction_result['predicted_disease'],
            confidence_score=prediction_result['confidence_score'],
            processing_time=prediction_result['processing_time'],
            image_size=image_info.get('dimensions', ''),
            file_size=image_info.get('file_size', 0)
        )

        return analysis


class AnalysisHistoryView(APIView):
    """
    Get analysis history for authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get list of user's analyses"""

        # Get only current user's analyses
        analyses = SkinAnalysis.objects.filter(user=request.user).order_by('-analysis_date')[:20]

        serializer = SkinAnalysisSerializer(
            analyses,
            many=True,
            context={'request': request}
        )

        return Response({
            'success': True,
            'count': len(serializer.data),
            'analyses': serializer.data,
            'user_info': {
                'total_analyses': request.user.analysis_count,
                'user_id': str(request.user.id)
            }
        }, status=status.HTTP_200_OK)


class AnalysisDetailView(APIView):
    """
    Get specific analysis details (user can only access their own)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, analysis_id):
        """Get details of specific analysis"""

        try:
            # Ensure user can only access their own analysis
            analysis = SkinAnalysis.objects.get(id=analysis_id, user=request.user)
            serializer = SkinAnalysisSerializer(analysis, context={'request': request})

            return Response({
                'success': True,
                'analysis': serializer.data
            }, status=status.HTTP_200_OK)

        except SkinAnalysis.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Analysis not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, analysis_id):
        """Delete specific analysis (user can only delete their own)"""

        try:
            analysis = SkinAnalysis.objects.get(id=analysis_id, user=request.user)

            # Delete image file if exists
            if analysis.image:
                if os.path.exists(analysis.image.path):
                    os.remove(analysis.image.path)

            # Delete analysis record
            analysis.delete()

            return Response({
                'success': True,
                'message': 'Analysis deleted successfully'
            }, status=status.HTTP_200_OK)

        except SkinAnalysis.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Analysis not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)


class SystemStatusView(APIView):
    """
    Check system status and available diseases (public endpoint)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Get system status"""

        return Response({
            'success': True,
            'status': 'operational',
            'ai_model': 'dummy_model_v1.0',
            'available_diseases': dummy_predictor.get_available_diseases(),
            'supported_formats': ['JPEG', 'JPG', 'PNG'],
            'max_file_size_mb': 5,
            'version': '1.0.0',
            'authentication_required': True,
            'endpoints': {
                'register': '/api/v1/auth/register/',
                'login': '/api/v1/auth/login/',
                'analyze': '/api/v1/skin-analysis/analyze/',
                'history': '/api/v1/skin-analysis/history/',
                'chatbot': '/api/v1/chatbot/start-chat/',
                'chat_status': '/api/v1/chatbot/status/',
            }
        }, status=status.HTTP_200_OK)


class UserAnalysisStatsView(APIView):
    """
    Get user's analysis statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's analysis statistics"""

        from django.db.models import Count, Avg
        from datetime import datetime, timedelta

        user = request.user

        # Basic stats
        total_analyses = SkinAnalysis.objects.filter(user=user).count()

        # Weekly stats
        week_ago = datetime.now() - timedelta(days=7)
        weekly_analyses = SkinAnalysis.objects.filter(
            user=user,
            analysis_date__gte=week_ago
        ).count()

        # Monthly stats
        month_ago = datetime.now() - timedelta(days=30)
        monthly_analyses = SkinAnalysis.objects.filter(
            user=user,
            analysis_date__gte=month_ago
        ).count()

        # Disease distribution
        disease_stats = SkinAnalysis.objects.filter(user=user) \
            .values('predicted_disease') \
            .annotate(count=Count('predicted_disease')) \
            .order_by('-count')

        # Average confidence
        avg_confidence = SkinAnalysis.objects.filter(user=user) \
            .aggregate(avg_confidence=Avg('confidence_score'))['avg_confidence']

        return Response({
            'success': True,
            'statistics': {
                'total_analyses': total_analyses,
                'weekly_analyses': weekly_analyses,
                'monthly_analyses': monthly_analyses,
                'average_confidence': round(avg_confidence * 100, 2) if avg_confidence else 0,
                'disease_distribution': list(disease_stats),
                'member_since': user.created_at.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)