from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('FOOD', 'Food'),
        ('BEVERAGE', 'Beverage'),
        ('CLEANING', 'Cleaning Supplies'),
        ('UTENSILS', 'Utensils'),
        ('OTHER', 'Other'),
    ]

    UNIT_CHOICES = [
        ('KG', 'Kilogram'),
        ('G', 'Gram'),
        ('L', 'Liter'),
        ('ML', 'Milliliter'),
        ('PCS', 'Pieces'),
        ('BOX', 'Box'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='items')
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=50, help_text="Storage location in the restaurant")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity_on_hand} {self.unit})"

    @property
    def needs_reorder(self):
        return self.quantity_on_hand <= self.reorder_level

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, help_text="Reference number or description")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        # Update item quantity based on transaction
        if self.transaction_type == 'IN':
            self.item.quantity_on_hand += self.quantity
        elif self.transaction_type == 'OUT':
            self.item.quantity_on_hand -= self.quantity
        elif self.transaction_type == 'ADJUST':
            self.item.quantity_on_hand = self.quantity
        self.item.save()
        super().save(*args, **kwargs)

class InventoryAlert(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')

    def __str__(self):
        return f"Alert for {self.item.name} - {self.status}"

    def resolve(self, user):
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()
