from django.contrib import admin
from .models import (
    Customer, Reservation, Order, POSTransaction,
    Inventory, MenuItem, OrderItem, Staff, Schedule
)

# Register models with proper verbose names
class InventoryAdmin(admin.ModelAdmin):
    verbose_name = 'Inventory Item'
    verbose_name_plural = 'Inventory Items'

class StaffAdmin(admin.ModelAdmin):
    verbose_name = 'Staff Member'
    verbose_name_plural = 'Staff Members'

class ScheduleAdmin(admin.ModelAdmin):
    verbose_name = 'Staff Schedule'
    verbose_name_plural = 'Staff Schedules'

admin.site.register(Customer)
admin.site.register(Reservation)
admin.site.register(Order)
admin.site.register(POSTransaction)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(MenuItem)
admin.site.register(OrderItem)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Schedule, ScheduleAdmin) 