from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    customerID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Cake(models.Model):
    CAKE_TYPES = [
        ('birthday', 'Birthday Cake'),
        ('wedding', 'Wedding Cake'),
        ('custom', 'Custom Cake'),
        ('pastry', 'Pastry'),
        ('cupcake', 'Cupcake'),
        ('cheesecake', 'Cheesecake'),
    ]
    FLAVORS = [
        ('vanilla', 'Vanilla'),
        ('chocolate', 'Chocolate'),
        ('strawberry', 'Strawberry'),
        ('red_velvet', 'Red Velvet'),
        ('lemon', 'Lemon'),
        ('carrot', 'Carrot'),
        ('mocha', 'Mocha'),
        ('ube', 'Ube'),
        ('pandan', 'Pandan'),
    ]
    SIZES = [
        ('4inch', '4 inch (2-4 servings)'),
        ('6inch', '6 inch (6-8 servings)'),
        ('8inch', '8 inch (10-12 servings)'),
        ('10inch', '10 inch (20-25 servings)'),
        ('12inch', '12 inch (30-35 servings)'),
        ('sheet', 'Sheet Cake (50+ servings)'),
    ]

    cakeID = models.AutoField(primary_key=True)
    caketype = models.CharField(max_length=50, choices=CAKE_TYPES)
    flavor = models.CharField(max_length=50, choices=FLAVORS)
    size = models.CharField(max_length=20, choices=SIZES)
    baseprice = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_caketype_display()} - {self.get_flavor_display()} ({self.get_size_display()})"

    class Meta:
        ordering = ['caketype', 'flavor']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    orderID = models.AutoField(primary_key=True)
    customerID = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    cakeID = models.ForeignKey(Cake, on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
    orderdate = models.DateField(auto_now_add=True)
    pickupdate = models.DateField()
    orderstatus = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    totalprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order #{self.orderID} - {self.customerID.name}"

    def calculate_total(self):
        total = sum(item.price for item in self.order_items.all())
        self.totalprice = total
        self.save()
        return total

    class Meta:
        ordering = ['-orderdate']


class OrderItem(models.Model):
    orderitemID = models.AutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    cakeID = models.ForeignKey(Cake, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    design_notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.cakeID} for Order #{self.orderID.orderID}"

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.cakeID.baseprice * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
    ]

    paymentID = models.AutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    paymentdate = models.DateField(auto_now_add=True)
    paymentmethod = models.CharField(max_length=20, choices=METHOD_CHOICES)
    paymentstatus = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment #{self.paymentID} - {self.get_paymentstatus_display()}"

    class Meta:
        ordering = ['-paymentdate']


class Staff(models.Model):
    ROLE_CHOICES = [
        ('baker', 'Baker'),
        ('decorator', 'Cake Decorator'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('delivery', 'Delivery'),
    ]

    staffID = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Staff'


class ProductionTask(models.Model):
    TASK_TYPES = [
        ('baking', 'Baking'),
        ('decorating', 'Decorating'),
        ('fondant', 'Fondant Work'),
        ('assembly', 'Assembly'),
        ('packaging', 'Packaging'),
        ('quality_check', 'Quality Check'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]

    taskID = models.AutoField(primary_key=True)
    orderitemID = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='tasks')
    staffID = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    productiondate = models.DateField()
    starttime = models.TimeField()
    endtime = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.orderitemID}"

    class Meta:
        ordering = ['productiondate', 'starttime']


class CustomerAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_account')
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='account', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Account: {self.user.username}"
