from django.urls import path
from hive.users.views import UserAPIView


urlpatterns = [
    path('', UserAPIView.as_view(), name='users'),
]
