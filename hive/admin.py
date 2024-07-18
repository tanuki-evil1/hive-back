from django import forms
from django.contrib import admin
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class AdminLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username or password")
        # Получите токен JWT
        refresh_token = RefreshToken.for_user(user)
        print(refresh_token)
        access_token = str(refresh_token)
        cleaned_data['token'] = access_token
        return cleaned_data


class AdminLoginAdmin(admin.ModelAdmin):
    form = AdminLoginForm


admin.site.register(AdminLoginForm, AdminLoginAdmin)
