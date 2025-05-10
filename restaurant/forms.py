from django import forms
from .models import (
    Reservation, Order, MenuItem, OrderItem,
    Category, Table, Payment, Staff, Schedule, Inventory, TimeOffRequest
)

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'table', 'date_time', 'number_of_guests',
            'special_requests', 'status'
        ]
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'special_requests': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table', 'status']
        widgets = {
            'table': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category', 'is_available', 
                 'preparation_time', 'image', 'stock_alert_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'preparation_time': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'stock_alert_threshold': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'special_instructions': forms.Textarea(attrs={'rows': 2}),
        }

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'position', 'contact_info', 'user']

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['staff', 'shift_date', 'shift_start_time', 'shift_end_time', 'hours_worked']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'shift_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'shift_end_time': forms.TimeInput(attrs={'type': 'time'}),
            'hours_worked': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method', 'transaction_id', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['number', 'capacity', 'is_available']
        widgets = {
            'number': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['item_name', 'quantity_on_hand', 'reorder_level', 'supplier_info']
        widgets = {
            'supplier_info': forms.Textarea(attrs={'rows': 3}),
        }

class TimeOffRequestForm(forms.ModelForm):
    class Meta:
        model = TimeOffRequest
        fields = ['staff', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        
class TimeOffRequestManagerForm(forms.ModelForm):
    class Meta:
        model = TimeOffRequest
        fields = ['staff', 'start_date', 'end_date', 'reason', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        } 