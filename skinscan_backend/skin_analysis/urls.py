from django.urls import path
from .views import (
    ImageAnalysisView,
    AnalysisHistoryView,
    AnalysisDetailView,
    SystemStatusView,
    UserAnalysisStatsView
)

app_name = 'skin_analysis'

urlpatterns = [
    # Main analysis endpoint (requires authentication)
    path('analyze/', ImageAnalysisView.as_view(), name='analyze-image'),

    # History and details (requires authentication)
    path('history/', AnalysisHistoryView.as_view(), name='analysis-history'),
    path('analysis/<uuid:analysis_id>/', AnalysisDetailView.as_view(), name='analysis-detail'),

    # User statistics (requires authentication)
    path('stats/', UserAnalysisStatsView.as_view(), name='user-analysis-stats'),

    # System status (public)
    path('status/', SystemStatusView.as_view(), name='system-status'),
]