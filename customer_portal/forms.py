from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomerFeedback, Payment, CustomerProfile
from restaurant.models import Reservation
from django.utils import timezone
from datetime import datetime, time, timedelta

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove all the help_text
        for field in self.fields:
            self.fields[field].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CustomerFeedbackForm(forms.ModelForm):
    class Meta:
        model = CustomerFeedback
        fields = ['rating', 'comment', 'is_public']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(),
        }

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['phone_number', 'address', 'preferred_payment_method']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class ReservationForm(forms.ModelForm):
    customer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name'
        })
    )
    
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your phone number'
        })
    )
    
    date_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
            'min': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'max': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')
        }),
        help_text='Select a date and time for your reservation (up to 30 days in advance)'
    )
    
    number_of_guests = forms.IntegerField(
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '20'
        }),
        help_text='Enter number of guests (1-20)'
    )
    
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requests or dietary requirements?'
        })
    )

    class Meta:
        model = Reservation
        fields = ['customer_name', 'customer_email', 'customer_phone', 'date_time', 'number_of_guests', 'special_requests']

    def clean_date_time(self):
        date_time = self.cleaned_data.get('date_time')
        if date_time:
            if date_time < timezone.now():
                raise forms.ValidationError("Reservation time cannot be in the past")
            if date_time > timezone.now() + timedelta(days=30):
                raise forms.ValidationError("Reservations can only be made up to 30 days in advance")
        return date_time

    def clean_number_of_guests(self):
        guests = self.cleaned_data['number_of_guests']
        if guests < 1:
            raise forms.ValidationError("Number of guests must be at least 1.")
        if guests > 20:
            raise forms.ValidationError("For parties larger than 20, please contact us directly.")
        return guests 