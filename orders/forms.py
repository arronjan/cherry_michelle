from django import forms
from .models import Customer, Cake, Order, OrderItem, Payment, Staff, ProductionTask


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'number', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Delivery Address'}),
        }


class CakeForm(forms.ModelForm):
    class Meta:
        model = Cake
        fields = ['caketype', 'flavor', 'size', 'baseprice', 'description', 'is_available']
        widgets = {
            'caketype': forms.Select(attrs={'class': 'form-select'}),
            'flavor': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'baseprice': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customerID', 'pickupdate', 'orderstatus', 'notes']
        widgets = {
            'customerID': forms.Select(attrs={'class': 'form-select'}),
            'pickupdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'orderstatus': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['cakeID', 'quantity', 'design_notes', 'price']
        widgets = {
            'cakeID': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'design_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['orderID', 'paymentmethod', 'paymentstatus', 'amount', 'reference_number']
        widgets = {
            'orderID': forms.Select(attrs={'class': 'form-select'}),
            'paymentmethod': forms.Select(attrs={'class': 'form-select'}),
            'paymentstatus': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'number', 'role', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductionTaskForm(forms.ModelForm):
    class Meta:
        model = ProductionTask
        fields = ['orderitemID', 'staffID', 'task_type', 'productiondate', 'starttime', 'endtime', 'status', 'notes']
        widgets = {
            'orderitemID': forms.Select(attrs={'class': 'form-select'}),
            'staffID': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'productiondate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'starttime': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'endtime': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
