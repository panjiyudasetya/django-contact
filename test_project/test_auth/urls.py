from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('auth/obtain-token/',
         TokenObtainPairView.as_view(),
         name='auth-login'),
    path('auth/refresh-token/',
         TokenRefreshView.as_view(),
         name='auth-refresh-token'),
]
