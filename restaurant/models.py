from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_info = models.TextField()

    def __str__(self):
        return self.customer_name

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('FOOD', 'Food'),
        ('BEVERAGE', 'Beverage'),
        ('CLEANING', 'Cleaning Supplies'),
        ('UTENSILS', 'Utensils'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='menu_items')
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=900, help_text="Preparation time in minutes")
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Inventory related fields
    ingredients = models.ManyToManyField('inventory.InventoryItem', through='MenuItemIngredient')
    stock_alert_threshold = models.PositiveIntegerField(default=10, help_text="Alert when stock falls below this number")

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        """Check if all required ingredients are in stock"""
        return all(ingredient.quantity_on_hand >= ingredient.quantity_required 
                  for ingredient in self.menu_item_ingredients.all())

class MenuItemIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='menu_item_ingredients')
    ingredient = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, choices=[
        ('KG', 'Kilogram'),
        ('G', 'Gram'),
        ('L', 'Liter'),
        ('ML', 'Milliliter'),
        ('PCS', 'Pieces'),
    ])

    def __str__(self):
        return f"{self.menu_item.name} - {self.ingredient.name}"

class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Table {self.number} (Capacity: {self.capacity})"

    def is_available_at(self, date_time, duration_minutes=120):
        """
        Check if the table is available at a specific date and time.
        By default, checks for 2-hour window around the requested time.
        """
        # Don't allow reservations in the past
        if date_time < timezone.now():
            return False

        # Check if table is marked as available
        if not self.is_available:
            return False

        # Calculate time window
        time_window_start = date_time - timedelta(minutes=duration_minutes/2)
        time_window_end = date_time + timedelta(minutes=duration_minutes/2)

        # Check for existing reservations in this time window
        existing_reservations = self.reservation_set.filter(
            status__in=['PENDING', 'CONFIRMED'],
            date_time__range=(time_window_start, time_window_end)
        ).exists()

        return not existing_reservations

    @classmethod
    def get_available_tables(cls, date_time, guests, duration_minutes=120):
        """
        Get all available tables that can accommodate the number of guests
        at the specified date and time.
        """
        # Get tables with sufficient capacity
        suitable_tables = cls.objects.filter(
            capacity__gte=guests,
            is_available=True
        )

        # Filter for availability at the specified time
        return [
            table for table in suitable_tables 
            if table.is_available_at(date_time, duration_minutes)
        ]

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(default="unknown@example.com")
    customer_phone = models.CharField(max_length=20)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    date_time = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reservation {self.reservation_id} - {self.customer_name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('SERVED', 'Served'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_id = models.AutoField(primary_key=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - Table {self.table.number if self.table else 'N/A'}"

    def update_total(self):
        """Update the total amount based on order items"""
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} for Order {self.order.order_id}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.update_total()

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('ONLINE', 'Online'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.order_id} - {self.amount}"

class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    quantity_on_hand = models.IntegerField()
    reorder_level = models.IntegerField()
    supplier_info = models.TextField()

    class Meta:
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'

    def __str__(self):
        return self.item_name

class Staff(models.Model):
    POSITION_CHOICES = [
        ('MANAGER', 'Manager'),
        ('WAITER', 'Waiter'),
        ('CHEF', 'Chef'),
        ('CASHIER', 'Cashier'),
    ]

    staff_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    contact_info = models.TextField()
    hire_date = models.DateField()
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'

    def __str__(self):
        return f"{self.name} - {self.position}"

class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    shift_date = models.DateField()
    shift_start_time = models.TimeField()
    shift_end_time = models.TimeField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = 'Staff Schedule'
        verbose_name_plural = 'Staff Schedules'

    def __str__(self):
        return f"{self.staff.name} - {self.shift_date}"

class POSTransaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('ONLINE', 'Online'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.payment_method}" 