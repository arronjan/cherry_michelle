from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth (staff)
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='orders/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Customer Auth
    path('register/', views.customer_register, name='customer_register'),
    path('customer/login/', views.customer_login_view, name='customer_login'),
    path('customer/logout/', views.customer_logout_view, name='customer_logout'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/menu/', views.customer_menu, name='customer_menu'),
    path('customer/order/place/', views.customer_place_order, name='customer_place_order'),
    path('customer/order/<int:pk>/', views.customer_order_detail, name='customer_order_detail'),

    # Staff - Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Staff - Cakes
    path('cakes/', views.cake_list, name='cake_list'),
    path('cakes/add/', views.cake_add, name='cake_add'),
    path('cakes/<int:pk>/edit/', views.cake_edit, name='cake_edit'),
    path('cakes/<int:pk>/delete/', views.cake_delete, name='cake_delete'),

    # Staff - Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/add/', views.order_add, name='order_add'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/update-status/', views.order_update_status, name='order_update_status'),

    # Staff - Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),

    # Staff - Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add_v2, name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),

    # Staff - Production
    path('production/', views.production_list, name='production_list'),
    path('production/add/', views.production_add, name='production_add'),
    path('production/<int:pk>/edit/', views.production_edit, name='production_edit'),
    path('production/<int:pk>/delete/', views.production_delete, name='production_delete'),
]
