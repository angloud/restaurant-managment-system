from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F
from django.contrib import messages
from itertools import groupby
from datetime import datetime, timedelta
from .models import (
    Reservation, Order, MenuItem, 
    Staff, Schedule, Inventory, OrderItem
)
from .forms import (
    ReservationForm, OrderForm, MenuItemForm,
    StaffForm, InventoryForm, OrderItemForm, ScheduleForm
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
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reservation updated successfully!')
            return redirect('restaurant:reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    
    return render(request, 'restaurant/reservations/form.html', {
        'form': form,
        'reservation': reservation
    })

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    reservation.delete()
    messages.success(request, 'Reservation deleted successfully!')
    return redirect('restaurant:reservation_list')

# Order Views
@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-order_time')
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
            special_requests = request.POST.getlist('special_requests[]')
            
            for item_id, qty, special in zip(menu_items, quantities, special_requests):
                if item_id and int(qty) > 0:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=item_id,
                        quantity=qty,
                        special_requests=special
                    )
            
            messages.success(request, 'Order created successfully!')
            return redirect('restaurant:order_list')
    else:
        form = OrderForm()
    
    menu_items = MenuItem.objects.all().order_by('category', 'item_name')
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
            order.orderitem_set.all().delete()
            
            # Process order items
            menu_items = request.POST.getlist('menu_item[]')
            quantities = request.POST.getlist('quantity[]')
            special_requests = request.POST.getlist('special_requests[]')
            
            for item_id, qty, special in zip(menu_items, quantities, special_requests):
                if item_id and int(qty) > 0:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=item_id,
                        quantity=qty,
                        special_requests=special
                    )
            
            messages.success(request, 'Order updated successfully!')
            return redirect('restaurant:order_list')
    else:
        form = OrderForm(instance=order)
    
    menu_items = MenuItem.objects.all().order_by('category', 'item_name')
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
    menu_items = MenuItem.objects.all().order_by('category', 'item_name')
    return render(request, 'restaurant/menu/list.html', {
        'menu_items': menu_items
    })

@login_required
def menu_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
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
        form = MenuItemForm(request.POST, instance=menu_item)
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
    menu_item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('restaurant:menu_list')

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
    inventory_item = get_object_or_404(Inventory, pk=pk)
    inventory_item.delete()
    messages.success(request, 'Inventory item deleted successfully!')
    return redirect('restaurant:inventory_list') 