from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)


urlpatterns = [
    path('auth/obtain-token/',
         TokenObtainPairView.as_view(),
         name='auth-obtain-token'),
    path('auth/blacklist-token/',
         TokenBlacklistView.as_view(),
         name='auth-blacklist-token'),
    path('auth/refresh-token/',
         TokenRefreshView.as_view(),
         name='auth-refresh-token'),
]
