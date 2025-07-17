"""
URL configuration for skinscan_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint"""
    return Response({
        'name': 'SkinScan API',
        'version': '1.0.0',
        'description': 'AI-powered skin disease detection and consultation system',
        'endpoints': {
            'authentication': '/api/v1/auth/',
            'skin_analysis': '/api/v1/skin-analysis/',
            'chatbot': '/api/v1/chatbot/',
            'admin': '/admin/',
        },
        'features': [
            'AI-powered skin disease detection',
            'User authentication and profiles',
            'Medical consultation chatbot',
            'Analysis history tracking'
        ],
        'documentation': 'Contact support for API documentation',
        'support': 'skinscan@support.com'
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Info
    path('api/', api_info, name='api-info'),
    path('api/v1/', api_info, name='api-v1-info'),

    # Authentication endpoints
    path('api/v1/auth/', include('skinscan_authentication.urls')),

    # Skin analysis endpoints
    path('api/v1/skin-analysis/', include('skin_analysis.urls')),

    # Chatbot endpoints
    path('api/v1/chatbot/', include('skinscan_chatbot.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)