from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'customer_portal'

urlpatterns = [
    path('', views.auth_page, name='auth_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('reservation/new/', views.make_reservation, name='make_reservation'),
    path('reservation/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('feedback/<int:reservation_id>/', views.submit_feedback, name='submit_feedback_reservation'),
    path('feedback/order/<int:order_id>/', views.submit_feedback, name='submit_feedback_order'),
    path('payment/reservation/<int:reservation_id>/', views.process_payment, name='process_payment_reservation'),
    path('payment/order/<int:order_id>/', views.process_payment, name='process_payment_order'),
    path('logout/', LogoutView.as_view(next_page='customer_portal:auth_page'), name='logout'),
] 