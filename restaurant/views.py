from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F, Sum, Count
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from itertools import groupby
from datetime import datetime, timedelta
from .models import (
    Reservation, Order, MenuItem, 
    Staff, Schedule, OrderItem, Category, Table, Payment, Inventory
)
from .forms import (
    ReservationForm, OrderForm, MenuItemForm,
    StaffForm, OrderItemForm, ScheduleForm,
    CategoryForm, TableForm, PaymentForm, InventoryForm
)

def home(request):
    today = timezone.now().date()
    
    context = {
        'today_reservations_count': Reservation.objects.filter(
            date_time__date=today
        ).count(),
        'active_orders_count': Order.objects.filter(
            status__in=['PENDING', 'PREPARING']
        ).count(),
        'staff_on_duty_count': Schedule.objects.filter(
            shift_date=today
        ).count(),
        'low_stock_count': Inventory.objects.filter(
            quantity_on_hand__lte=F('reorder_level')
        ).count(),
        'recent_activities': []  # We'll implement this later
    }
    
    return render(request, 'restaurant/home.html', context)

# Reservation Views
@login_required
def reservation_list(request):
    reservations = Reservation.objects.all().order_by('-date_time')
    return render(request, 'restaurant/reservations/list.html', {
        'reservations': reservations
    })

@login_required
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    old_status = reservation.status
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            updated_reservation = form.save()
            
            # Check if status changed to CONFIRMED and send email
            if old_status != 'CONFIRMED' and updated_reservation.status == 'CONFIRMED':
                send_reservation_confirmation_email(updated_reservation)
                messages.success(request, f'Reservation confirmed! Confirmation email sent to {updated_reservation.customer_email}')
            # Check if status changed to CANCELLED
            elif old_status != 'CANCELLED' and updated_reservation.status == 'CANCELLED':
                send_reservation_cancellation_email(updated_reservation)
                messages.success(request, f'Reservation cancelled! Notification email sent to {updated_reservation.customer_email}')
            else:
                messages.success(request, 'Reservation updated successfully!')
                
            return redirect('restaurant:reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    
    return render(request, 'restaurant/reservations/form.html', {
        'form': form,
        'reservation': reservation
    })

def send_reservation_confirmation_email(reservation):
    """Send a confirmation email to the customer when their reservation is confirmed."""
    subject = 'Your Reservation is Confirmed!'
    table_info = f"Table {reservation.table.number}" if reservation.table else "Your table"
    formatted_date = reservation.date_time.strftime('%A, %B %d, %Y at %I:%M %p')
    
    message = f"""
    Dear {reservation.customer_name},
    
    We're pleased to confirm your reservation at our restaurant!
    
    Reservation Details:
    -------------------
    Date and Time: {formatted_date}
    Number of Guests: {reservation.number_of_guests}
    {table_info}
    
    Special Requests: {reservation.special_requests if reservation.special_requests else 'None'}
    
    We look forward to welcoming you to our restaurant. If you need to make any changes to your reservation, please contact us as soon as possible.
    
    Thank you for choosing our restaurant!
    
    Best regards,
    The Restaurant Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [reservation.customer_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error but don't stop execution
        print(f"Error sending confirmation email: {str(e)}")
        return False

def send_reservation_cancellation_email(reservation):
    """Send a notification email to the customer when their reservation is cancelled."""
    subject = 'Your Reservation has been Cancelled'
    formatted_date = reservation.date_time.strftime('%A, %B %d, %Y at %I:%M %p')
    
    message = f"""
    Dear {reservation.customer_name},
    
    We regret to inform you that your reservation at our restaurant has been cancelled.
    
    Cancelled Reservation Details:
    ----------------------------
    Date and Time: {formatted_date}
    Number of Guests: {reservation.number_of_guests}
    
    If you believe this cancellation was made in error or would like to make a new reservation, please contact us.
    
    Thank you for your understanding.
    
    Best regards,
    The Restaurant Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [reservation.customer_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error but don't stop execution
        print(f"Error sending cancellation email: {str(e)}")
        return False

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    reservation.delete()
    messages.success(request, 'Reservation deleted successfully!')
    return redirect('restaurant:reservation_list')

# Order Views
@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'restaurant/orders/list.html', {
        'orders': orders
    })

@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'PENDING'
            order.save()
            
            # Process order items
            menu_items = request.POST.getlist('menu_item[]')
            quantities = request.POST.getlist('quantity[]')
            special_instructions = request.POST.getlist('special_instructions[]')
            
            for item_id, qty, special in zip(menu_items, quantities, special_instructions):
                if item_id and int(qty) > 0:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=item_id,
                        quantity=qty,
                        special_instructions=special
                    )
            
            messages.success(request, 'Order created successfully!')
            return redirect('restaurant:order_list')
    else:
        form = OrderForm()
    
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    return render(request, 'restaurant/orders/form.html', {
        'form': form,
        'menu_items': menu_items
    })

@login_required
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            
            # Clear existing items
            order.items.all().delete()
            
            # Process order items
            menu_items = request.POST.getlist('menu_item[]')
            quantities = request.POST.getlist('quantity[]')
            special_instructions = request.POST.getlist('special_instructions[]')
            
            for item_id, qty, special in zip(menu_items, quantities, special_instructions):
                if item_id and int(qty) > 0:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=item_id,
                        quantity=qty,
                        special_instructions=special
                    )
            
            messages.success(request, 'Order updated successfully!')
            return redirect('restaurant:order_list')
    else:
        form = OrderForm(instance=order)
    
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    return render(request, 'restaurant/orders/form.html', {
        'form': form,
        'menu_items': menu_items,
        'order': order,
        'is_update': True
    })

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, 'Order deleted successfully!')
    return redirect('restaurant:order_list')

# Menu Views
@login_required
def menu_list(request):
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    return render(request, 'restaurant/menu/list.html', {
        'menu_items': menu_items
    })

@login_required
def menu_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item created successfully!')
            return redirect('restaurant:menu_list')
    else:
        form = MenuItemForm()
    
    return render(request, 'restaurant/menu/form.html', {
        'form': form
    })

@login_required
def menu_update(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('restaurant:menu_list')
    else:
        form = MenuItemForm(instance=menu_item)
    
    return render(request, 'restaurant/menu/form.html', {
        'form': form,
        'menu_item': menu_item
    })

@login_required
def menu_delete(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        menu_item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('restaurant:menu_list')
    return render(request, 'restaurant/menu/delete.html', {'menu_item': menu_item})

# Staff Views
@login_required
def staff_schedule(request):
    schedules = Schedule.objects.all().order_by('shift_date')
    return render(request, 'restaurant/staff/schedule.html', {
        'schedules': schedules
    })

@login_required
def schedule_create(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff schedule created successfully!')
            return redirect('restaurant:staff_schedule')
    else:
        form = ScheduleForm()
    
    return render(request, 'restaurant/staff/form.html', {
        'form': form
    })

@login_required
def schedule_update(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff schedule updated successfully!')
            return redirect('restaurant:staff_schedule')
    else:
        form = ScheduleForm(instance=schedule)
    
    return render(request, 'restaurant/staff/form.html', {
        'form': form,
        'schedule': schedule
    })

@login_required
def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    schedule.delete()
    messages.success(request, 'Staff schedule deleted successfully!')
    return redirect('restaurant:staff_schedule')

# Inventory Views
@login_required
def inventory_list(request):
    inventory_items = Inventory.objects.all().order_by('item_name')
    return render(request, 'restaurant/inventory/list.html', {
        'inventory_items': inventory_items
    })

@login_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item created successfully!')
            return redirect('restaurant:inventory_list')
    else:
        form = InventoryForm()
    
    return render(request, 'restaurant/inventory/form.html', {
        'form': form
    })

@login_required
def inventory_update(request, pk):
    inventory_item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated successfully!')
            return redirect('restaurant:inventory_list')
    else:
        form = InventoryForm(instance=inventory_item)
    
    return render(request, 'restaurant/inventory/form.html', {
        'form': form,
        'inventory_item': inventory_item
    })

@login_required
def inventory_delete(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        inventory.delete()
        messages.success(request, 'Inventory item deleted successfully!')
        return redirect('restaurant:inventory_list')
    return render(request, 'restaurant/inventory_delete.html', {'inventory': inventory})

# Table Management
@login_required
def table_list(request):
    tables = Table.objects.all().order_by('number')
    return render(request, 'restaurant/table_list.html', {'tables': tables})

@login_required
def table_create(request):
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table created successfully!')
            return redirect('restaurant:table_list')
    else:
        form = TableForm()
    return render(request, 'restaurant/table_form.html', {'form': form, 'action': 'Create'})

@login_required
def table_update(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table updated successfully!')
            return redirect('restaurant:table_list')
    else:
        form = TableForm(instance=table)
    return render(request, 'restaurant/table_form.html', {'form': form, 'table': table, 'action': 'Update'})

@login_required
def table_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        table.delete()
        messages.success(request, 'Table deleted successfully!')
        return redirect('restaurant:table_list')
    return render(request, 'restaurant/table_delete.html', {'table': table}) 