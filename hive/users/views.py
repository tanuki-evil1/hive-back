from django.shortcuts import render
from rest_framework import generics
from hive.users.models import User
from hive.users.serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated


# Create your views here.
class UserAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer
