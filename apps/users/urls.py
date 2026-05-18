"""URL configuration for the users app."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.views import RegisterView, CurrentUserView, PasswordChangeView

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current user
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('password/', PasswordChangeView.as_view(), name='password_change'),
]
