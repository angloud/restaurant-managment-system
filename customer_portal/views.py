from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from .forms import (
    CustomerRegistrationForm, CustomerFeedbackForm,
    PaymentForm, CustomerProfileForm, ReservationForm
)
from .models import CustomerFeedback, Payment, CustomerProfile
from restaurant.models import Reservation, Order, Customer, Table
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

def auth_page(request):
    if request.method == 'POST':
        if 'login' in request.POST:
            login_form = CustomAuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                # Ensure customer profile exists
                Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        'customer_name': f"{user.first_name} {user.last_name}",
                        'customer_info': f'Customer since {timezone.now().strftime("%Y-%m-%d")}'
                    }
                )
                return redirect('customer_portal:dashboard')
            register_form = CustomerRegistrationForm()
            active_tab = 'login'
        elif 'register' in request.POST:
            register_form = CustomerRegistrationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                # Create customer profile if it doesn't exist
                Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        'customer_name': f"{user.first_name} {user.last_name}",
                        'customer_info': f'Customer since {timezone.now().strftime("%Y-%m-%d")}'
                    }
                )
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to our restaurant portal.')
                return redirect('customer_portal:dashboard')
            login_form = CustomAuthenticationForm()
            active_tab = 'register'
    else:
        login_form = CustomAuthenticationForm()
        register_form = CustomerRegistrationForm()
        active_tab = 'login'

    return render(request, 'customer_portal/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
        'active_tab': active_tab
    })

@login_required
def make_reservation(request):
    # Get the customer information
    user = request.user
    customer = get_object_or_404(Customer, user=user)
    
    # Try to get phone number from profile, if exists
    try:
        profile = CustomerProfile.objects.get(user=user)
        phone = profile.phone_number
    except CustomerProfile.DoesNotExist:
        phone = ""
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.customer_name = form.cleaned_data.get('customer_name', f"{user.first_name} {user.last_name}")
            reservation.customer_email = user.email
            reservation.customer_phone = form.cleaned_data.get('customer_phone', phone)
            reservation.status = 'PENDING'
            reservation.save()
            
            messages.success(request, 'Your reservation has been submitted successfully! Please check your email for confirmation.')
            return redirect('customer_portal:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Prefill the form with customer data
        initial_data = {
            'customer_name': f"{user.first_name} {user.last_name}",
            'customer_email': user.email,
            'customer_phone': phone,
        }
        form = ReservationForm(initial=initial_data)
    
    return render(request, 'customer_portal/make_reservation.html', {'form': form})

@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, customer_email=request.user.email)
    return render(request, 'customer_portal/reservation_detail.html', {
        'reservation': reservation
    })

@login_required
def submit_feedback(request, reservation_id=None, order_id=None):
    if request.method == 'POST':
        form = CustomerFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.customer = request.user
            if reservation_id:
                feedback.reservation = get_object_or_404(Reservation, pk=reservation_id)
            if order_id:
                feedback.order = get_object_or_404(Order, pk=order_id)
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('customer_portal:dashboard')
    else:
        form = CustomerFeedbackForm()
    return render(request, 'customer_portal/submit_feedback.html', {'form': form})

@login_required
def process_payment(request, reservation_id=None, order_id=None):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            if reservation_id:
                payment.reservation = get_object_or_404(Reservation, pk=reservation_id)
                payment.amount = 50  # Example amount for reservation deposit
            if order_id:
                payment.order = get_object_or_404(Order, pk=order_id)
                payment.amount = payment.order.total_amount
            payment.status = 'COMPLETED'  # In real implementation, this would be set after payment gateway confirmation
            payment.save()
            messages.success(request, 'Payment processed successfully!')
            return redirect('customer_portal:dashboard')
    else:
        form = PaymentForm()
    return render(request, 'customer_portal/process_payment.html', {'form': form})

@login_required
def profile(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('customer_portal:profile')
    else:
        form = CustomerProfileForm(instance=profile)
    return render(request, 'customer_portal/profile.html', {'form': form})

@login_required
def dashboard(request):
    customer = get_object_or_404(Customer, user=request.user)
    
    # Get customer's reservations
    reservations = Reservation.objects.filter(
        customer_email=request.user.email
    ).order_by('-date_time')[:5]
    
    # Get customer's orders through their reservations
    orders = Order.objects.filter(
        table__reservation__customer_email=request.user.email
    ).order_by('-created_at')[:5]
    
    # Get customer's feedback using the User instance
    feedback = CustomerFeedback.objects.filter(
        customer=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'customer': customer,
        'reservations': reservations,
        'orders': orders,
        'feedback': feedback,
    }
    
    return render(request, 'customer_portal/dashboard.html', context)
