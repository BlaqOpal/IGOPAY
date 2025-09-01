from django.shortcuts import render, redirect
from .forms import UserRegisterForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import random
from django.core.mail import send_mail

# Create your views here.

def RegisterView(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Hey {username}, your account was created successfully.")
            new_user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect("core:index")
    if request.user.is_authenticated:
        messages.warning(request, f" You are already logged in.")
        return redirect("core:index")
    else:
        form = UserRegisterForm()
    return render(request, 'userauths/sign-up.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def LoginView(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            next_url = request.GET.get('next', 'account:dashboard')  # Redirect to next or dashboard
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "userauths/sign-in.html")

def LogoutView(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect('userauths:sign-in')
        
      
class ReAuthenticateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stored_otp = request.session.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        if not stored_otp or not otp_expiry or timezone.now() > otp_expiry:
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['otp_expiry'] = timezone.now() + timezone.timedelta(minutes=5)

            # Send OTP to email
            send_mail(
                subject='Your OTP for Re-Authentication',
                message=f'Your OTP is {otp}. It expires in 5 minutes.',
                from_email='your-email@gmail.com',  # Replace with settings.DEFAULT_FROM_EMAIL if needed
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            messages.success(request, "A new OTP has been sent to your email.")

        return render(request, 'userauths/re-authenticate.html')

    def post(self, request):
        action = request.POST.get('action')
        otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        if action == 'resend':
            new_otp = str(random.randint(100000, 999999))
            request.session['otp'] = new_otp
            request.session['otp_expiry'] = timezone.now() + timezone.timedelta(minutes=5)

            send_mail(
                subject='Your New OTP for Re-Authentication',
                message=f'Your new OTP is {new_otp}. It expires in 5 minutes.',
                from_email='your-email@gmail.com',
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            messages.success(request, "A new OTP has been sent to your email.")
            return render(request, 'userauths/re-authenticate.html')

        if not otp:
            return render(request, 'userauths/re-authenticate.html', {'error': 'OTP is required.'})

        if not stored_otp or not otp_expiry or timezone.now() > otp_expiry:
            return render(request, 'userauths/re-authenticate.html', {'error': 'OTP expired or invalid.'})

        if otp == stored_otp:
            del request.session['otp']
            del request.session['otp_expiry']
            request.session['re_authenticated'] = True
            return redirect('core:index')  # Redirect to a protected or dashboard view

        return render(request, 'userauths/re-authenticate.html', {'error': 'Invalid OTP. Please try again.'})

        
        from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages

def SignUpView(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('account:dashboard')
    else:
        form = UserCreationForm()
    return render(request, "userauths/sign-up.html", {'form': form})