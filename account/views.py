from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import KYCForm
from .models import KYC, Account
from core.forms import CreditCardForm
from core.models import CreditCard, Transaction
from django.conf import settings  # For settings.AUTH_USER_MODEL (optional verification)

# Ensure only authenticated users can access this view
@login_required
def account(request):
    user = request.user
    try:
        kyc = KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        messages.warning(request, "You Need To Submit Your KYC")
        return redirect("account:kyc-reg")
    except Exception as e:
        messages.error(request, f"Error retrieving KYC: {str(e)}")
        return redirect("account:kyc-reg")

    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        messages.error(request, "No account found. Please contact support.")
        return redirect("account:dashboard")

    context = {
        'account': account,
        'kyc': kyc,
    }
    return render(request, 'account/account.html', context)

# Ensure only authenticated users can access this view
@login_required
def kyc_registration(request):
    user = request.user
    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        messages.error(request, "No account found. Please create an account first.")
        return redirect("account:dashboard")

    try:
        kyc = KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        kyc = None

    if request.method == "POST":
        form = KYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = user
            new_form.account = account
            new_form.save()
            messages.success(request, "KYC Form submitted successfully")
            return redirect("account:dashboard")
    else:
        form = KYCForm(instance=kyc)

    context = {
        "account": account,
        "form": form,
        "kyc": kyc,
    }
    return render(request, "account/kyc-form.html", context)

# Ensure only authenticated users can access this view
@login_required
def Dashboard(request):
    user = request.user
    try:
        kyc = KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        messages.warning(request, "You Need To Submit Your KYC")
        return redirect("account:kyc-reg")
    except Exception as e:
        messages.error(request, f"Error retrieving KYC: {str(e)}")
        return redirect("account:kyc-reg")

    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        messages.error(request, "No account found. Please contact support.")
        return redirect("account:dashboard")

    recent_transfer = Transaction.objects.filter(sender=user, transaction_type="transfer", status="completed").order_by("-id")[:1]
    recent_recieved_transfer = Transaction.objects.filter(reciver=user, transaction_type="transfer").order_by("-id")[:1]
    sender_transaction = Transaction.objects.filter(sender=user, transaction_type="transfer").order_by("-id")
    reciever_transaction = Transaction.objects.filter(reciver=user, transaction_type="transfer").order_by("-id")
    request_sender_transaction = Transaction.objects.filter(sender=user, transaction_type="request")
    request_reciever_transaction = Transaction.objects.filter(reciver=user, transaction_type="request")
    credit_card = CreditCard.objects.filter(user=user).order_by("-id")

    if request.method == "POST":
        form = CreditCardForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = user
            new_form.save()
            messages.success(request, "Card Added Successfully.")
            return redirect("account:dashboard")
    else:
        form = CreditCardForm()

    context = {
        'account': account,
        'kyc': kyc,
        'form': form,
        'credit_card': credit_card,
        'sender_transaction': sender_transaction,
        'reciever_transaction': reciever_transaction,
        'request_sender_transaction': request_sender_transaction,
        'request_reciever_transaction': request_reciever_transaction,
        'recent_transfer': recent_transfer,
        'recent_recieved_transfer': recent_recieved_transfer,
    }
    return render(request, 'account/dashboard.html', context)