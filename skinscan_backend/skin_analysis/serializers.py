from rest_framework import serializers
from .models import SkinAnalysis


class SkinAnalysisSerializer(serializers.ModelSerializer):
    confidence_percentage = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SkinAnalysis
        fields = [
            'id',
            'predicted_disease',
            'confidence_score',
            'confidence_percentage',
            'analysis_date',
            'processing_time',
            'image_size',
            'file_size',
            'image_url'
        ]
        read_only_fields = ['id', 'analysis_date']

    def get_confidence_percentage(self, obj):
        """Return confidence as percentage"""
        return obj.confidence_percentage

    def get_image_url(self, obj):
        """Return image URL if available"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate_image(self, value):
        """Validate uploaded image"""

        # Check file size (5MB limit)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Image file size cannot exceed 5MB."
            )

        # Check file format
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        if value.image.format.upper() not in allowed_formats:
            raise serializers.ValidationError(
                "Only JPEG and PNG image formats are allowed."
            )

        # Check image dimensions (minimum size)
        if value.image.width < 100 or value.image.height < 100:
            raise serializers.ValidationError(
                "Image dimensions must be at least 100x100 pixels."
            )

        return value