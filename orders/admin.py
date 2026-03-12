from django.contrib import admin
from .models import Customer, Cake, Order, OrderItem, Payment, Staff, ProductionTask


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customerID', 'name', 'number', 'email', 'created_at']
    search_fields = ['name', 'email', 'number']
    list_filter = ['created_at']


@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = ['cakeID', 'caketype', 'flavor', 'size', 'baseprice', 'is_available']
    list_filter = ['caketype', 'flavor', 'is_available']
    search_fields = ['caketype', 'flavor']
    list_editable = ['baseprice', 'is_available']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['cakeID', 'quantity', 'design_notes', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['orderID', 'customerID', 'orderdate', 'pickupdate', 'orderstatus', 'totalprice']
    list_filter = ['orderstatus', 'orderdate', 'pickupdate']
    search_fields = ['customerID__name', 'orderID']
    inlines = [OrderItemInline]
    readonly_fields = ['orderdate']
    list_editable = ['orderstatus']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['paymentID', 'orderID', 'paymentdate', 'paymentmethod', 'paymentstatus', 'amount']
    list_filter = ['paymentstatus', 'paymentmethod']
    search_fields = ['orderID__orderID', 'reference_number']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['staffID', 'name', 'role', 'number', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']


class ProductionTaskAdmin(admin.ModelAdmin):
    list_display = ['taskID', 'orderitemID', 'staffID', 'task_type', 'productiondate', 'status']
    list_filter = ['status', 'task_type', 'productiondate']
    search_fields = ['staffID__name']
    list_editable = ['status']

admin.site.register(ProductionTask, ProductionTaskAdmin)

# Customize admin site header
admin.site.site_header = "Cherry Michelle's Cakes & Pastries"
admin.site.site_title = "Cakery Admin"
admin.site.index_title = "Bakery Management System"
