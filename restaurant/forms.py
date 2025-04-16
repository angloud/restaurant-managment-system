from django import forms
from .models import (
    Reservation, Order, MenuItem, 
    Staff, Inventory, OrderItem, Schedule
)

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer', 'table_number', 'date_time', 'number_of_guests']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table_number']
        widgets = {
            'table_number': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['item_name', 'description', 'price', 'category']

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'position', 'contact_info', 'hire_date']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['item_name', 'quantity_on_hand', 'reorder_level', 'supplier_info']

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_requests']

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['staff', 'shift_date', 'shift_start_time', 'shift_end_time']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'shift_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'shift_end_time': forms.TimeInput(attrs={'type': 'time'}),
        } 