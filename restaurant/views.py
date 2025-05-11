from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F, Sum, Count
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from itertools import groupby
from datetime import datetime, timedelta, date
from .models import (
    Reservation, Order, MenuItem, 
    Staff, Schedule, OrderItem, Category, Table, Payment, Inventory, TimeOffRequest
)
from .forms import (
    ReservationForm, OrderForm, MenuItemForm,
    StaffForm, OrderItemForm, ScheduleForm,
    CategoryForm, TableForm, PaymentForm, InventoryForm,
    TimeOffRequestManagerForm, TimeOffRequestForm
)
from django.contrib.auth import logout

def home(request):
    today = timezone.now().date()
    
    context = {
        'today_reservations_count': Reservation.objects.filter(
            date_time__date=today
        ).count(),
        'active_orders_count': Order.objects.filter(
            status__in=['PENDING', 'PREPARING']
        ).count(),
        'ready_orders_count': Order.objects.filter(
            status='READY'
        ).count(),
        'preparing_orders_count': Order.objects.filter(
            status='PREPARING'
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
        # Create a copy of POST data to modify
        post_data = request.POST.copy()
        # Set a default status if not provided
        if 'status' not in post_data or not post_data['status']:
            post_data['status'] = 'PENDING'
            
        form = OrderForm(post_data)
        if form.is_valid():
            order = form.save()
            
            # Process order items
            menu_items = request.POST.getlist('menu_item[]')
            quantities = request.POST.getlist('quantity[]')
            special_instructions = request.POST.getlist('special_instructions[]')
            
            # Debug information
            print(f"Menu items: {menu_items}")
            print(f"Quantities: {quantities}")
            print(f"Special instructions: {special_instructions}")
            
            # Check if we have any items to process
            if not menu_items or len(menu_items) == 0:
                messages.warning(request, 'Order created but no items were added.')
                return redirect('restaurant:order_list')
                
            for item_id, qty, special in zip(menu_items, quantities, special_instructions):
                if item_id and int(qty) > 0:
                    try:
                        OrderItem.objects.create(
                            order=order,
                            menu_item_id=item_id,
                            quantity=qty,
                            special_instructions=special
                        )
                        print(f"Created order item: {item_id}, qty: {qty}")
                    except Exception as e:
                        print(f"Error creating order item: {str(e)}")
                        messages.error(request, f"Error adding item to order: {str(e)}")
            
            messages.success(request, 'Order created successfully!')
            return redirect('restaurant:order_list')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")
    else:
        form = OrderForm(initial={'status': 'PENDING'})
    
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
            
            # Debug information
            print(f"Update - Menu items: {menu_items}")
            print(f"Update - Quantities: {quantities}")
            print(f"Update - Special instructions: {special_instructions}")
            
            # Check if we have any items to process
            if not menu_items or len(menu_items) == 0:
                messages.warning(request, 'Order updated but no items were added.')
                return redirect('restaurant:order_list')
                
            for item_id, qty, special in zip(menu_items, quantities, special_instructions):
                if item_id and int(qty) > 0:
                    try:
                        OrderItem.objects.create(
                            order=order,
                            menu_item_id=item_id,
                            quantity=qty,
                            special_instructions=special
                        )
                        print(f"Updated order item: {item_id}, qty: {qty}")
                    except Exception as e:
                        print(f"Error updating order item: {str(e)}")
                        messages.error(request, f"Error updating item in order: {str(e)}")
            
            messages.success(request, 'Order updated successfully!')

            # Notify kitchen staff if status changed to READY
            if order.status == 'READY':
                messages.info(request, 'Kitchen staff has been notified that the order is ready.')
                # Send notification logic would go here
            
            return redirect('restaurant:order_list')
        else:
            print(f"Update form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")
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
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order deleted successfully!')
        return redirect('restaurant:order_list')
    return render(request, 'restaurant/orders/delete.html', {'order': order})

@login_required
def order_detail(request, pk):
    """View order details including all items"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'restaurant/orders/detail.html', {'order': order})

@login_required
def kitchen_dashboard(request):
    """Kitchen staff dashboard to view and update order status"""
    pending_orders = Order.objects.filter(status='PENDING').order_by('-created_at')
    preparing_orders = Order.objects.filter(status='PREPARING').order_by('-created_at')
    ready_orders = Order.objects.filter(status='READY').order_by('-created_at')
    
    return render(request, 'restaurant/orders/kitchen.html', {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders
    })

@login_required
def order_update_status(request, pk):
    """Update order status quickly from kitchen dashboard"""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get('status')
        
        if status in [s[0] for s in Order.STATUS_CHOICES]:
            previous_status = order.status
            order.status = status
            order.save()
            
            # Add success message
            messages.success(request, f'Order #{order.order_id} updated to {order.get_status_display()}')
            
            # Notify staff if the order is ready
            if status == 'READY' and previous_status != 'READY':
                messages.info(request, 'Staff has been notified that the order is ready for delivery.')
                # Send notification logic would go here
                
        return redirect('restaurant:kitchen_dashboard')
    
    return redirect('restaurant:kitchen_dashboard')

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
def staff_list(request):
    """View all staff members"""
    staff_members = Staff.objects.all().order_by('name')
    return render(request, 'restaurant/staff/list.html', {
        'staff_members': staff_members
    })

@login_required
def staff_create(request):
    """Create a new staff member"""
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member created successfully!')
            return redirect('restaurant:staff_list')
    else:
        form = StaffForm()
    
    return render(request, 'restaurant/staff/staff_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def staff_update(request, pk):
    """Update an existing staff member"""
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member updated successfully!')
            return redirect('restaurant:staff_list')
    else:
        form = StaffForm(instance=staff)
    
    return render(request, 'restaurant/staff/staff_form.html', {
        'form': form,
        'staff': staff,
        'action': 'Update'
    })

@login_required
def staff_delete(request, pk):
    """Delete a staff member"""
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff member deleted successfully!')
        return redirect('restaurant:staff_list')
    return render(request, 'restaurant/staff/staff_delete.html', {'staff': staff})

@login_required
def staff_schedule(request):
    """View all staff schedules"""
    schedules = Schedule.objects.all().order_by('shift_date')
    return render(request, 'restaurant/staff/schedule.html', {
        'schedules': schedules
    })

@login_required
def staff_schedule_calendar(request):
    """View staff schedules in a calendar format"""
    import calendar
    from datetime import datetime, timedelta, date
    
    # Get the month and year from the request, default to current month/year
    now = timezone.now()
    month = int(request.GET.get('month', now.month))
    year = int(request.GET.get('year', now.year))
    
    # Create a calendar for the month
    cal = calendar.monthcalendar(year, month)
    
    # Get month name
    month_name = calendar.month_name[month]
    
    # Calculate previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
        
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    # Get all schedules for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    schedules = Schedule.objects.filter(
        shift_date__gte=start_date,
        shift_date__lt=end_date
    ).select_related('staff')
    
    # Organize schedules by date
    schedule_by_date = {}
    for schedule in schedules:
        date_str = schedule.shift_date.strftime('%Y-%m-%d')
        if date_str not in schedule_by_date:
            schedule_by_date[date_str] = []
        schedule_by_date[date_str].append(schedule)
    
    # Generate calendar days
    calendar_days = []
    today = timezone.now().date()
    
    # Add days from previous month if needed
    first_day_weekday = calendar.monthrange(year, month)[0]
    if first_day_weekday > 0:
        # Get the last few days from the previous month
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
            
        prev_month_days = calendar.monthrange(prev_year, prev_month)[1]
        for i in range(first_day_weekday):
            day = prev_month_days - first_day_weekday + i + 1
            current_date = date(prev_year, prev_month, day)
            date_str = current_date.strftime('%Y-%m-%d')
            
            calendar_days.append({
                'day': day,
                'date': current_date,
                'today': current_date == today,
                'other_month': True,
                'shifts': schedule_by_date.get(date_str, [])
            })
    
    # Add days from current month
    month_days = calendar.monthrange(year, month)[1]
    for day in range(1, month_days + 1):
        current_date = date(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')
        
        calendar_days.append({
            'day': day,
            'date': current_date,
            'today': current_date == today,
            'other_month': False,
            'shifts': schedule_by_date.get(date_str, [])
        })
    
    # Add days from next month if needed
    days_so_far = len(calendar_days)
    if days_so_far % 7 != 0:
        days_to_add = 7 - (days_so_far % 7)
        
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        for day in range(1, days_to_add + 1):
            current_date = date(next_year, next_month, day)
            date_str = current_date.strftime('%Y-%m-%d')
            
            calendar_days.append({
                'day': day,
                'date': current_date,
                'today': current_date == today,
                'other_month': True,
                'shifts': schedule_by_date.get(date_str, [])
            })
    
    return render(request, 'restaurant/staff/schedule_calendar.html', {
        'schedules': schedules,
        'calendar_days': calendar_days,
        'current_month': month_name,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year
    })

@login_required
def schedule_create(request):
    """Create a new staff schedule"""
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
    """Update an existing staff schedule"""
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
    """Delete a staff schedule"""
    schedule = get_object_or_404(Schedule, pk=pk)
    schedule.delete()
    messages.success(request, 'Staff schedule deleted successfully!')
    return redirect('restaurant:staff_schedule')

@login_required
def my_schedule(request):
    """View own staff schedule"""
    # Get the staff member associated with the current user
    try:
        staff = Staff.objects.get(user=request.user)
        schedules = Schedule.objects.filter(staff=staff).order_by('shift_date')
        return render(request, 'restaurant/staff/my_schedule.html', {
            'schedules': schedules,
            'staff': staff
        })
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('restaurant:home')

# Time-off Request Views
@login_required
def time_off_request_list(request):
    """View all time-off requests (for managers)"""
    time_off_requests = TimeOffRequest.objects.all().order_by('-created_at')
    return render(request, 'restaurant/staff/time_off_request_list.html', {
        'time_off_requests': time_off_requests
    })

@login_required
def time_off_request_create(request):
    """Create a new time-off request"""
    # Try to get the staff member associated with the current user
    try:
        staff = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        # If no staff member is associated, check if the user is a manager
        if request.user.is_staff or request.user.is_superuser:
            if request.method == 'POST':
                form = TimeOffRequestManagerForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Time-off request created successfully!')
                    return redirect('restaurant:time_off_request_list')
            else:
                form = TimeOffRequestManagerForm()
            
            return render(request, 'restaurant/staff/time_off_request_form.html', {
                'form': form,
                'action': 'Create'
            })
        else:
            messages.error(request, 'You are not registered as a staff member.')
            return redirect('restaurant:home')
    
    # If we got here, the user is a staff member
    if request.method == 'POST':
        form = TimeOffRequestForm(request.POST)
        if form.is_valid():
            time_off_request = form.save(commit=False)
            time_off_request.staff = staff
            time_off_request.save()
            messages.success(request, 'Time-off request submitted successfully!')
            return redirect('restaurant:my_time_off_requests')
    else:
        form = TimeOffRequestForm(initial={'staff': staff})
        # Disable the staff field since we're setting it automatically
        form.fields['staff'].disabled = True
    
    return render(request, 'restaurant/staff/time_off_request_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def time_off_request_update(request, pk):
    """Update an existing time-off request"""
    time_off_request = get_object_or_404(TimeOffRequest, pk=pk)
    
    # Check if the user is the staff member who created this request or a manager
    is_manager = request.user.is_staff or request.user.is_superuser
    is_owner = hasattr(request.user, 'staff') and request.user.staff == time_off_request.staff
    
    if not (is_manager or is_owner):
        messages.error(request, 'You do not have permission to edit this time-off request.')
        return redirect('restaurant:home')
    
    if request.method == 'POST':
        # Use different form based on role
        if is_manager:
            form = TimeOffRequestManagerForm(request.POST, instance=time_off_request)
        else:
            form = TimeOffRequestForm(request.POST, instance=time_off_request)
            
        if form.is_valid():
            form.save()
            messages.success(request, 'Time-off request updated successfully!')
            
            # Redirect based on role
            if is_manager:
                return redirect('restaurant:time_off_request_list')
            else:
                return redirect('restaurant:my_time_off_requests')
    else:
        # Use different form based on role
        if is_manager:
            form = TimeOffRequestManagerForm(instance=time_off_request)
        else:
            form = TimeOffRequestForm(instance=time_off_request)
            # Disable staff field for regular staff
            form.fields['staff'].disabled = True
    
    return render(request, 'restaurant/staff/time_off_request_form.html', {
        'form': form,
        'time_off_request': time_off_request,
        'action': 'Update'
    })

@login_required
def time_off_request_delete(request, pk):
    """Delete a time-off request"""
    time_off_request = get_object_or_404(TimeOffRequest, pk=pk)
    
    # Check if the user is the staff member who created this request or a manager
    is_manager = request.user.is_staff or request.user.is_superuser
    is_owner = hasattr(request.user, 'staff') and request.user.staff == time_off_request.staff
    
    if not (is_manager or is_owner):
        messages.error(request, 'You do not have permission to delete this time-off request.')
        return redirect('restaurant:home')
    
    if request.method == 'POST':
        time_off_request.delete()
        messages.success(request, 'Time-off request deleted successfully!')
        
        # Redirect based on role
        if is_manager:
            return redirect('restaurant:time_off_request_list')
        else:
            return redirect('restaurant:my_time_off_requests')
            
    return render(request, 'restaurant/staff/time_off_request_delete.html', {
        'time_off_request': time_off_request
    })

@login_required
def my_time_off_requests(request):
    """View own time-off requests"""
    # Get the staff member associated with the current user
    try:
        staff = Staff.objects.get(user=request.user)
        time_off_requests = TimeOffRequest.objects.filter(staff=staff).order_by('-created_at')
        return render(request, 'restaurant/staff/my_time_off_requests.html', {
            'time_off_requests': time_off_requests,
            'staff': staff
        })
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('restaurant:home')

@login_required
def time_off_request_approve(request, pk):
    """Approve a time-off request (for managers only)"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to approve time-off requests.')
        return redirect('restaurant:home')
        
    time_off_request = get_object_or_404(TimeOffRequest, pk=pk)
    time_off_request.status = 'APPROVED'
    time_off_request.save()
    
    messages.success(request, f'Time-off request from {time_off_request.staff.name} has been approved.')
    return redirect('restaurant:time_off_request_list')

@login_required
def time_off_request_reject(request, pk):
    """Reject a time-off request (for managers only)"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to reject time-off requests.')
        return redirect('restaurant:home')
        
    time_off_request = get_object_or_404(TimeOffRequest, pk=pk)
    time_off_request.status = 'REJECTED'
    time_off_request.save()
    
    messages.success(request, f'Time-off request from {time_off_request.staff.name} has been rejected.')
    return redirect('restaurant:time_off_request_list')

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

@login_required
def inventory_usage_report(request):
    """
    Generate inventory usage report to help with planning and reducing waste.
    """
    # Get date range parameters from request or set defaults
    from_date_str = request.GET.get('from_date', '')
    to_date_str = request.GET.get('to_date', '')
    
    # Set default date range to the past 30 days if not provided
    if not from_date_str or not to_date_str:
        to_date = timezone.now().date()
        from_date = to_date - timedelta(days=30)
    else:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            to_date = timezone.now().date()
            from_date = to_date - timedelta(days=30)
    
    # Fetch orders in the date range
    orders = Order.objects.filter(
        created_at__date__gte=from_date,
        created_at__date__lte=to_date
    )
    
    # Collect order items and count by menu item
    order_items = OrderItem.objects.filter(order__in=orders)
    
    # Aggregate data by menu item
    menu_item_usage = {}
    for item in order_items:
        menu_item_name = item.menu_item.name
        if menu_item_name not in menu_item_usage:
            menu_item_usage[menu_item_name] = {
                'quantity': 0,
                'menu_item_id': item.menu_item.id,
                'revenue': 0
            }
        menu_item_usage[menu_item_name]['quantity'] += item.quantity
        menu_item_usage[menu_item_name]['revenue'] += item.subtotal
    
    # Sort by usage (most used first)
    sorted_items = sorted(menu_item_usage.items(), key=lambda x: x[1]['quantity'], reverse=True)
    
    # Connect to inventory data
    for item_name, data in menu_item_usage.items():
        menu_item = MenuItem.objects.get(id=data['menu_item_id'])
        data['category'] = menu_item.category.name if menu_item.category else 'Uncategorized'
    
    # Get low stock items
    low_stock_items = Inventory.objects.filter(
        quantity_on_hand__lte=F('reorder_level')
    ).order_by('item_name')
    
    context = {
        'from_date': from_date,
        'to_date': to_date,
        'sorted_items': sorted_items,
        'low_stock_items': low_stock_items,
        'total_orders': orders.count(),
        'total_revenue': sum(data['revenue'] for _, data in menu_item_usage.items())
    }
    
    return render(request, 'restaurant/inventory/usage_report.html', context)

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

def logout_view(request):
    """Custom logout view that handles both GET and POST requests."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully!")
    return redirect('restaurant:home')

@login_required
def pos_integration(request):
    """Simple POS integration demonstration for academic purposes."""
    # Get recent orders for demonstration
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Mock POS connection status
    pos_status = {
        'connected': True,
        'system_name': 'RestaurantPOS Pro',
        'version': '2.5.1',
        'last_sync': timezone.now(),
        'terminal_count': 3,
    }
    
    # Mock daily sales data
    from random import randint
    sales_data = {
        'cash_sales': randint(500, 1500),
        'card_sales': randint(1000, 3000),
        'online_sales': randint(300, 800),
        'total_sales': 0,
        'transaction_count': randint(30, 100),
    }
    sales_data['total_sales'] = sales_data['cash_sales'] + sales_data['card_sales'] + sales_data['online_sales']
    
    context = {
        'recent_orders': recent_orders,
        'pos_status': pos_status,
        'sales_data': sales_data,
    }
    
    return render(request, 'restaurant/pos/integration.html', context) 