
from django.urls import path
from .views import UserAPIView, UserLogin, UserLogout

urlpatterns = [
    path('', UserAPIView.as_view(), name='users'),
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', UserLogout.as_view(), name='logout'),
]
