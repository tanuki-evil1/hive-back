from django.contrib.auth import authenticate, login, logout
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

from integrations_test.active_directory.domain_controller import ActiveDirectory


# Create your views here.
class UserAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        print(username, password)
        user_in_db = User.objects.filter(username=username).exists()
        if not user_in_db:  # Если пользователь в бд еще не сохранен - сохраняем
            ad = ActiveDirectory('hive.com')
            user_data = ad.get_user_base_data(username, password)
            User.objects.create_user(first_name=user_data['first_name'], last_name=user_data['last_name'],
                                     username=user_data['username'], email=user_data['email'], password=password)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return Response({'message': 'Logged in successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class UserLogout(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)