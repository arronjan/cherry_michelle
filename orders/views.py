from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Customer, Cake, Order, OrderItem, Payment, Staff, ProductionTask
from .forms import CustomerForm, CakeForm, OrderForm, OrderItemForm, PaymentForm, StaffForm, ProductionTaskForm
from django.contrib.auth.models import User as AuthUser
from .forms import StaffCreationForm

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


# ============================================================
# CUSTOMER PORTAL VIEWS
# ============================================================
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomerRegistrationForm, CustomerOrderForm
from .models import CustomerAccount


def home(request):
    """Public landing page - redirect based on user type"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'customer_account'):
            return redirect('customer_dashboard')
        return redirect('dashboard')
    return render(request, 'orders/home.html')


def customer_register(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
    form = CustomerRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        # Create linked Customer record
        customer = Customer.objects.create(
            name=form.cleaned_data['name'],
            email=form.cleaned_data['email'],
            number=form.cleaned_data['number'],
            address=form.cleaned_data['address'],
        )
        CustomerAccount.objects.create(user=user, customer=customer)
        login(request, user)
        messages.success(request, f'Welcome, {customer.name}! Your account has been created.')
        return redirect('customer_dashboard')
    return render(request, 'orders/customer_register.html', {'form': form})


def customer_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'customer_account'):
            return redirect('customer_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if hasattr(user, 'customer_account'):
                return redirect('customer_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'orders/customer_login.html')


def customer_logout_view(request):
    logout(request)
    return redirect('home')


def customer_dashboard(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    orders = Order.objects.filter(customerID=customer).order_by('-orderdate')
    return render(request, 'orders/customer_dashboard.html', {
        'customer': customer,
        'orders': orders,
    })


def customer_menu(request):
    cakes = Cake.objects.filter(is_available=True).order_by('caketype', 'flavor')
    cake_types = {}
    for cake in cakes:
        t = cake.get_caketype_display()
        if t not in cake_types:
            cake_types[t] = []
        cake_types[t].append(cake)
    return render(request, 'orders/customer_menu.html', {'cake_types': cake_types})


def customer_place_order(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    form = CustomerOrderForm(request.POST or None)
    if form.is_valid():
        cake = form.cleaned_data['cake']
        quantity = form.cleaned_data['quantity']
        order = Order.objects.create(
            customerID=customer,
            cakeID=cake,
            pickupdate=form.cleaned_data['pickupdate'],
            orderstatus='pending',
            totalprice=cake.baseprice * quantity,
        )
        OrderItem.objects.create(
            orderID=order,
            cakeID=cake,
            quantity=quantity,
            design_notes=form.cleaned_data['design_notes'],
            price=cake.baseprice * quantity,
        )
        messages.success(request, f'Order #{order.orderID} placed successfully! We will confirm it shortly.')
        return redirect('customer_order_detail', pk=order.pk)
    return render(request, 'orders/customer_place_order.html', {'form': form})


def customer_order_detail(request, pk):
    if not request.user.is_authenticated or not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)
    items = order.order_items.select_related('cakeID').all()
    payments = order.payments.all()
    return render(request, 'orders/customer_order_detail.html', {
        'order': order, 'items': items, 'payments': payments
    })


@login_required
def staff_add_v2(request):
    form = StaffCreationForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        if AuthUser.objects.filter(username=username).exists():
            form.add_error('username', 'Username already exists.')
        else:
            user = AuthUser.objects.create_user(username=username, password=password)
            staff = form.save(commit=False)
            staff.user = user
            staff.save()
            messages.success(request, f'Staff account for {staff.name} created!')
            return redirect('staff_list')
    return render(request, 'orders/staff_add.html', {'form': form, 'title': 'Add Staff Account'})