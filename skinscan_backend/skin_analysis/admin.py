from django.contrib import admin
from .models import SkinAnalysis


@admin.register(SkinAnalysis)
class SkinAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'predicted_disease',
        'confidence_percentage',
        'analysis_date',
        'processing_time',
        'user_email'  # Updated to show email instead of username
    ]
    list_filter = [
        'predicted_disease',
        'analysis_date'
    ]
    search_fields = [
        'predicted_disease',
        'user__email',  # Updated to search by email
        'user__username'
    ]
    readonly_fields = [
        'id',
        'analysis_date',
        'processing_time'
    ]

    def confidence_percentage(self, obj):
        return f"{obj.confidence_percentage}%"

    confidence_percentage.short_description = 'Confidence'

    def user_email(self, obj):
        return obj.user.email if obj.user else 'Anonymous'

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'