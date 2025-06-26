from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.account, name='account'),
    path('kyc-reg/', views.kyc_registration, name='kyc-reg'),
    path('dashboard/', views.Dashboard, name='dashboard'),
]