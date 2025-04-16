from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomerFeedback, Payment, CustomerProfile

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
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

class ReservationForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    number_of_guests = forms.IntegerField(min_value=1, max_value=20)
    special_requests = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    ) 