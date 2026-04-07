from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from .models import Customer, Cake, Order, OrderItem, Payment, Staff, ProductionTask
from .forms import CustomerForm, CakeForm, OrderForm, OrderItemForm, PaymentForm, StaffForm, ProductionTaskForm
from django.contrib.auth.models import User as AuthUser
from .forms import StaffCreationForm
import random
import string
import json
import urllib.request as urllib_request
import urllib.parse
import base64

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
        order.payments.all().delete()  # Delete related payments first
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
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can delete staff.')
        return redirect('staff_list')
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
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can add production tasks.')
        return redirect('production_list')
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
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can delete production tasks.')
        return redirect('production_list')
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
        Payment.objects.create(
            orderID=order,
            paymentmethod=form.cleaned_data['payment_method'],
            paymentstatus='pending',
            amount=cake.baseprice * quantity,
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
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can add staff.')
        return redirect('staff_list')
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

# --- USER MANAGEMENT ---
@login_required
def user_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can access this.')
        return redirect('dashboard')
    users = AuthUser.objects.all().order_by('username')
    return render(request, 'orders/user_list.html', {'users': users})


@login_required
def user_add(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can access this.')
        return redirect('dashboard')
    from .forms import StaffCreationForm
    form = StaffCreationForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        if AuthUser.objects.filter(username=username).exists():
            form.add_error('username', 'Username already exists.')
        else:
            user = AuthUser.objects.create_user(username=username, password=password)
            user.is_superuser = form.cleaned_data.get('is_manager', False)
            user.is_staff = form.cleaned_data.get('is_manager', False)
            user.save()
            staff = form.save(commit=False)
            staff.user = user
            staff.save()
            messages.success(request, f'User {username} created!')
            return redirect('user_list')
    return render(request, 'orders/user_add.html', {'form': form})


@login_required
def user_edit(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can access this.')
        return redirect('dashboard')
    user = get_object_or_404(AuthUser, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('password')
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        if new_password:
            user.set_password(new_password)
        user.is_superuser = is_superuser
        user.is_active = is_active
        user.save()
        messages.success(request, f'User {user.username} updated!')
        return redirect('user_list')
    return render(request, 'orders/user_edit.html', {'edited_user': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can access this.')
        return redirect('dashboard')
    user = get_object_or_404(AuthUser, pk=pk)
    if request.user == user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('user_list')
    return render(request, 'orders/confirm_delete.html', {'object': user, 'back_url': 'user_list'})


# --- REPORTS ---
@login_required
def reports(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only managers can view reports.')
        return redirect('dashboard')
    from django.db.models import Sum
    from datetime import date
    today = date.today()
    this_month_start = today.replace(day=1)
    stats = {
        'total_revenue': Payment.objects.filter(paymentstatus='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'month_revenue': Payment.objects.filter(paymentstatus='paid', paymentdate__gte=this_month_start).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_orders': Order.objects.count(),
        'completed_orders': Order.objects.filter(orderstatus='completed').count(),
        'cancelled_orders': Order.objects.filter(orderstatus='cancelled').count(),
        'pending_orders': Order.objects.filter(orderstatus='pending').count(),
        'total_customers': Customer.objects.count(),
        'total_staff': Staff.objects.filter(is_active=True).count(),
        'total_cakes': Cake.objects.filter(is_available=True).count(),
        'cash_payments': Payment.objects.filter(paymentmethod='cash', paymentstatus='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'gcash_payments': Payment.objects.filter(paymentmethod='gcash', paymentstatus='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'paypal_payments': Payment.objects.filter(paymentmethod='paypal', paymentstatus='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    top_cakes = Cake.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]
    recent_payments = Payment.objects.select_related('orderID__customerID').order_by('-paymentdate')[:10]
    orders_by_status = Order.objects.values('orderstatus').annotate(count=Count('orderstatus'))
    return render(request, 'orders/reports.html', {
        'stats': stats,
        'top_cakes': top_cakes,
        'recent_payments': recent_payments,
        'orders_by_status': orders_by_status,
    })

def generate_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

@login_required
def payment_simulation(request, pk):
    if not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)
    payment = order.payments.first()

    if payment and payment.paymentstatus == 'paid':
        messages.error(request, 'This order has already been paid.')
        return redirect('customer_order_detail', pk=pk)

    return render(request, 'orders/payment_simulation.html', {
        'order': order,
        'payment': payment,
    })


@login_required
def paypal_simulation(request, pk):
    if not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)
    payment = order.payments.first()
    return render(request, 'orders/paypal_simulation.html', {
        'order': order,
        'payment': payment,
        'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID,
    })


@csrf_exempt
@login_required
def paypal_capture(request, pk):
    """Called via AJAX from the PayPal JS SDK after buyer approves payment."""
    if not hasattr(request.user, 'customer_account'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
        paypal_order_id = body.get('orderID')
        if not paypal_order_id:
            return JsonResponse({'error': 'Missing orderID'}, status=400)

        # Get PayPal access token
        credentials = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        base_url = "https://api-m.sandbox.paypal.com"

        token_req = urllib_request.Request(
            f"{base_url}/v1/oauth2/token",
            data=b"grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib_request.urlopen(token_req) as resp:
            token_data = json.loads(resp.read())
        access_token = token_data["access_token"]

        # Capture the PayPal order
        capture_req = urllib_request.Request(
            f"{base_url}/v2/checkout/orders/{paypal_order_id}/capture",
            data=b"{}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        capture_req.get_method = lambda: "POST"
        with urllib_request.urlopen(capture_req) as resp:
            capture_data = json.loads(resp.read())

        if capture_data.get("status") == "COMPLETED":
            capture_id = capture_data["purchase_units"][0]["payments"]["captures"][0]["id"]
            payment = order.payments.first()
            if payment:
                payment.paymentstatus = 'paid'
                payment.paymentmethod = 'paypal'
                payment.reference_number = capture_id
                payment.save()
            else:
                Payment.objects.create(
                    orderID=order,
                    paymentmethod='paypal',
                    paymentstatus='paid',
                    amount=order.totalprice,
                    reference_number=capture_id,
                )
            return JsonResponse({'status': 'success', 'capture_id': capture_id})
        else:
            return JsonResponse({'error': 'Payment not completed', 'details': capture_data}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def cash_simulation(request, pk):
    if not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)
    payment = order.payments.first()

    if request.method == 'POST':
        if payment:
            payment.paymentstatus = 'pending'
            payment.paymentmethod = 'cash'
            payment.save()
        else:
            Payment.objects.create(
                orderID=order,
                paymentmethod='cash',
                paymentstatus='pending',
                amount=order.totalprice,
            )
        return redirect('payment_success', pk=pk)

    return render(request, 'orders/cash_simulation.html', {
        'order': order,
        'payment': payment,
    })


@login_required
def payment_success(request, pk):
    if not hasattr(request.user, 'customer_account'):
        return redirect('customer_login')
    customer = request.user.customer_account.customer
    order = get_object_or_404(Order, pk=pk, customerID=customer)
    payment = order.payments.first()
    return render(request, 'orders/payment_success.html', {
        'order': order,
        'payment': payment,
    })