from django.db import models
from django.conf import settings
import uuid


class SkinAnalysis(models.Model):
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User relationship - Updated to use custom user model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    # Image storage
    image = models.ImageField(upload_to='skin_images/%Y/%m/%d/')

    # Analysis results
    predicted_disease = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    # Metadata
    analysis_date = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds

    # Additional fields
    image_size = models.CharField(max_length=50, blank=True)  # e.g., "1920x1080"
    file_size = models.IntegerField(null=True, blank=True)  # in bytes

    class Meta:
        ordering = ['-analysis_date']
        verbose_name = 'Skin Analysis'
        verbose_name_plural = 'Skin Analyses'

    def __str__(self):
        return f"Analysis {self.id} - {self.predicted_disease or 'Pending'}"

    @property
    def confidence_percentage(self):
        """Return confidence as percentage"""
        if self.confidence_score:
            return round(self.confidence_score * 100, 2)
        return 0