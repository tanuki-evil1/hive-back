
from django.urls import path
from .views import UserAPIView, UserLogin

urlpatterns = [
    path('', UserAPIView.as_view(), name='users'),
    path('login/', UserLogin.as_view(), name='login'), # Добавил путь, пока не знаю куда лучше в основу или тут
]
