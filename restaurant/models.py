from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=100)
    customer_info = models.TextField()

    def __str__(self):
        return self.customer_name

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    table_number = models.IntegerField()
    date_time = models.DateTimeField()
    number_of_guests = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Reservation {self.reservation_id} - {self.customer.customer_name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready'),
        ('SERVED', 'Served'),
        ('COMPLETED', 'Completed'),
    ]

    order_id = models.AutoField(primary_key=True)
    table_number = models.IntegerField()
    order_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Order {self.order_id} - Table {self.table_number}"

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('APPETIZER', 'Appetizer'),
        ('MAIN', 'Main Course'),
        ('DESSERT', 'Dessert'),
        ('BEVERAGE', 'Beverage'),
    ]

    menu_item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    class Meta:
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'

    def __str__(self):
        return self.item_name

class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    special_requests = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.item_name}"

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