from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Customer, Cake, Order, OrderItem, Payment, Staff, ProductionTask
from .forms import CustomerForm, CakeForm, OrderForm, OrderItemForm, PaymentForm, StaffForm, ProductionTaskForm


@login_required
def dashboard(request):
    today = date.today()
    week_ahead = today + timedelta(days=7)

    stats = {
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(orderstatus='pending').count(),
        'in_production': Order.objects.filter(orderstatus='in_production').count(),
        'ready_orders': Order.objects.filter(orderstatus='ready').count(),
        'today_pickups': Order.objects.filter(pickupdate=today).count(),
        'week_pickups': Order.objects.filter(pickupdate__range=[today, week_ahead]).count(),
        'total_customers': Customer.objects.count(),
        'total_revenue': Payment.objects.filter(paymentstatus='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'active_tasks': ProductionTask.objects.filter(status__in=['scheduled', 'in_progress']).count(),
        'staff_count': Staff.objects.filter(is_active=True).count(),
    }

    recent_orders = Order.objects.select_related('customerID').order_by('-orderdate')[:8]
    upcoming_pickups = Order.objects.filter(
        pickupdate__gte=today, pickupdate__lte=week_ahead
    ).exclude(orderstatus='completed').select_related('customerID').order_by('pickupdate')[:6]
    today_tasks = ProductionTask.objects.filter(
        productiondate=today
    ).select_related('staffID', 'orderitemID__cakeID').order_by('starttime')[:8]

    return render(request, 'orders/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
        'upcoming_pickups': upcoming_pickups,
        'today_tasks': today_tasks,
        'today': today,
    })


# --- CUSTOMERS ---
@login_required
def customer_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(number__icontains=q))
    return render(request, 'orders/customer_list.html', {'customers': customers, 'q': q})

@login_required
def customer_add(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Customer added successfully!')
        return redirect('customer_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Add Customer', 'back_url': 'customer_list'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        messages.success(request, 'Customer updated!')
        return redirect('customer_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Edit Customer', 'back_url': 'customer_list'})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted.')
        return redirect('customer_list')
    return render(request, 'orders/confirm_delete.html', {'object': customer, 'back_url': 'customer_list'})


# --- CAKES ---
@login_required
def cake_list(request):
    cakes = Cake.objects.all()
    return render(request, 'orders/cake_list.html', {'cakes': cakes})

@login_required
def cake_add(request):
    form = CakeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cake added to menu!')
        return redirect('cake_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Add Cake', 'back_url': 'cake_list'})

@login_required
def cake_edit(request, pk):
    cake = get_object_or_404(Cake, pk=pk)
    form = CakeForm(request.POST or None, instance=cake)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cake updated!')
        return redirect('cake_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Edit Cake', 'back_url': 'cake_list'})

@login_required
def cake_delete(request, pk):
    cake = get_object_or_404(Cake, pk=pk)
    if request.method == 'POST':
        cake.delete()
        messages.success(request, 'Cake removed from menu.')
        return redirect('cake_list')
    return render(request, 'orders/confirm_delete.html', {'object': cake, 'back_url': 'cake_list'})


# --- ORDERS ---
@login_required
def order_list(request):
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '')
    orders = Order.objects.select_related('customerID').all()
    if status_filter:
        orders = orders.filter(orderstatus=status_filter)
    if q:
        orders = orders.filter(Q(customerID__name__icontains=q) | Q(orderID__icontains=q))
    return render(request, 'orders/order_list.html', {
        'orders': orders, 'status_filter': status_filter, 'q': q,
        'status_choices': Order.STATUS_CHOICES
    })

@login_required
def order_add(request):
    form = OrderForm(request.POST or None)
    if form.is_valid():
        order = form.save()
        messages.success(request, f'Order #{order.orderID} created!')
        return redirect('order_detail', pk=order.pk)
    return render(request, 'orders/form.html', {'form': form, 'title': 'New Order', 'back_url': 'order_list'})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    items = order.order_items.select_related('cakeID').all()
    payments = order.payments.all()
    tasks = ProductionTask.objects.filter(orderitemID__orderID=order).select_related('staffID')
    item_form = OrderItemForm()
    return render(request, 'orders/order_detail.html', {
        'order': order, 'items': items, 'payments': payments,
        'tasks': tasks, 'item_form': item_form
    })

@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, 'Order updated!')
        return redirect('order_detail', pk=pk)
    return render(request, 'orders/form.html', {'form': form, 'title': f'Edit Order #{pk}', 'back_url': 'order_list'})

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order deleted.')
        return redirect('order_list')
    return render(request, 'orders/confirm_delete.html', {'object': order, 'back_url': 'order_list'})

@login_required
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.orderstatus = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_orderstatus_display()}')
    return redirect('order_detail', pk=pk)


# --- PAYMENTS ---
@login_required
def payment_list(request):
    payments = Payment.objects.select_related('orderID__customerID').all()
    return render(request, 'orders/payment_list.html', {'payments': payments})

@login_required
def payment_add(request):
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Payment recorded!')
        return redirect('payment_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Record Payment', 'back_url': 'payment_list'})

@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    form = PaymentForm(request.POST or None, instance=payment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Payment updated!')
        return redirect('payment_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Edit Payment', 'back_url': 'payment_list'})


# --- STAFF ---
@login_required
def staff_list(request):
    staff = Staff.objects.all()
    return render(request, 'orders/staff_list.html', {'staff': staff})

@login_required
def staff_add(request):
    form = StaffForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Staff member added!')
        return redirect('staff_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Add Staff', 'back_url': 'staff_list'})

@login_required
def staff_edit(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    form = StaffForm(request.POST or None, instance=staff)
    if form.is_valid():
        form.save()
        messages.success(request, 'Staff updated!')
        return redirect('staff_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Edit Staff', 'back_url': 'staff_list'})

@login_required
def staff_delete(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff removed.')
        return redirect('staff_list')
    return render(request, 'orders/confirm_delete.html', {'object': staff, 'back_url': 'staff_list'})


# --- PRODUCTION ---
@login_required
def production_list(request):
    date_filter = request.GET.get('date', '')
    tasks = ProductionTask.objects.select_related('staffID', 'orderitemID__orderID__customerID', 'orderitemID__cakeID').all()
    if date_filter:
        tasks = tasks.filter(productiondate=date_filter)
    return render(request, 'orders/production_list.html', {'tasks': tasks, 'date_filter': date_filter})

@login_required
def production_add(request):
    form = ProductionTaskForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Production task scheduled!')
        return redirect('production_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Schedule Task', 'back_url': 'production_list'})

@login_required
def production_edit(request, pk):
    task = get_object_or_404(ProductionTask, pk=pk)
    form = ProductionTaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task updated!')
        return redirect('production_list')
    return render(request, 'orders/form.html', {'form': form, 'title': 'Edit Task', 'back_url': 'production_list'})

@login_required
def production_delete(request, pk):
    task = get_object_or_404(ProductionTask, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('production_list')
    return render(request, 'orders/confirm_delete.html', {'object': task, 'back_url': 'production_list'})
