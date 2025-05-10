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
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/create/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/update/', views.staff_update, name='staff_update'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('staff/schedule/', views.staff_schedule, name='staff_schedule'),
    path('staff/schedule/calendar/', views.staff_schedule_calendar, name='staff_schedule_calendar'),
    path('staff/schedule/create/', views.schedule_create, name='schedule_create'),
    path('staff/schedule/<int:pk>/update/', views.schedule_update, name='schedule_update'),
    path('staff/schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    path('staff/my-schedule/', views.my_schedule, name='my_schedule'),
    
    # Time-off Requests
    path('staff/time-off-requests/', views.time_off_request_list, name='time_off_request_list'),
    path('staff/time-off-requests/create/', views.time_off_request_create, name='time_off_request_create'),
    path('staff/time-off-requests/<int:pk>/update/', views.time_off_request_update, name='time_off_request_update'),
    path('staff/time-off-requests/<int:pk>/delete/', views.time_off_request_delete, name='time_off_request_delete'),
    path('staff/time-off-requests/<int:pk>/approve/', views.time_off_request_approve, name='time_off_request_approve'),
    path('staff/time-off-requests/<int:pk>/reject/', views.time_off_request_reject, name='time_off_request_reject'),
    path('staff/my-time-off-requests/', views.my_time_off_requests, name='my_time_off_requests'),
    
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