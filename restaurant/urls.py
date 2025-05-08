from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Reservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/<int:pk>/update/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),
    
    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/update/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('orders/<int:pk>/update-status/', views.order_update_status, name='order_update_status'),
    
    # Menu
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/create/', views.menu_create, name='menu_create'),
    path('menu/<int:pk>/update/', views.menu_update, name='menu_update'),
    path('menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),
    
    # Staff
    path('staff/schedule/', views.staff_schedule, name='staff_schedule'),
    path('staff/schedule/create/', views.schedule_create, name='schedule_create'),
    path('staff/schedule/<int:pk>/update/', views.schedule_update, name='schedule_update'),
    path('staff/schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/create/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/update/', views.inventory_update, name='inventory_update'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),
    
    # Tables
    path('tables/', views.table_list, name='table_list'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/<int:pk>/update/', views.table_update, name='table_update'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),
] 