from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserProfileUpdateView,
    PasswordChangeView,
    UserAnalysisHistoryView,
    UserDashboardView,
    DeleteAccountView
)

app_name = 'skinscan_authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Profile management
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),

    # User data and history
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
    path('history/', UserAnalysisHistoryView.as_view(), name='user-analysis-history'),

    # Account management
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
]