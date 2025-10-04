from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TokenObtainPairView, TokenRefreshView, MeView, RegisterView, LoginView, UsersListView, UsersAdminViewSet

router = DefaultRouter()
router.register(r'admin/users', UsersAdminViewSet, basename='admin-users')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UsersListView.as_view(), name='auth_users_list'),
    path('', include(router.urls)),
]
