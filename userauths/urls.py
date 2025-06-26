from django.urls import path
from . import views

app_name = 'userauths'

urlpatterns = [
    path('register/', views.RegisterView, name='register'),
    path('login/', views.LoginView, name='sign-in'),
    path('logout/', views.LogoutView, name='logout'),
    path('sign-up/', views.SignUpView, name='sign-up'),
    # path('re-authenticate/', views.re_authenticate, name='re-authenticate'),
]