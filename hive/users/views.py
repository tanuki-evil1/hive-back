from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from rest_framework import generics

from .forms import UserLoginForm
from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated

from integrations_test.active_directory.domain_controller import ActiveDirectory


# Create your views here.
class UserAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserLogin(View):
    def get(self, request, *args, **kwargs):  # Отдаем форму, надо бы переписать компактнее этот класс
        form = UserLoginForm()
        return render(request, 'login.html', {'form': form})  # Почему-то login.html не индексируется во внешней папке

    def post(self, request, *args, **kwargs):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_in_db = User.objects.filter(username=username).exists()
            if not user_in_db:  # Если пользователь в бд еще не сохранен - сохраняем
                ad = ActiveDirectory('hive.com')
                user_data = ad.get_user_base_data(username, password)
                User.objects.create_user(first_name=user_data['first_name'], last_name=user_data['last_name'],
                                         username=user_data['username'], email=user_data['email'], password=password)

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('users')
            else:
                return HttpResponse('Неправильные данные')

        return render(request, 'login.html', {'form': form})
