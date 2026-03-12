from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('customerID', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('number', models.CharField(max_length=20)),
                ('email', models.EmailField(unique=True)),
                ('address', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Cake',
            fields=[
                ('cakeID', models.AutoField(primary_key=True, serialize=False)),
                ('caketype', models.CharField(choices=[('birthday', 'Birthday Cake'), ('wedding', 'Wedding Cake'), ('custom', 'Custom Cake'), ('pastry', 'Pastry'), ('cupcake', 'Cupcake'), ('cheesecake', 'Cheesecake')], max_length=50)),
                ('flavor', models.CharField(choices=[('vanilla', 'Vanilla'), ('chocolate', 'Chocolate'), ('strawberry', 'Strawberry'), ('red_velvet', 'Red Velvet'), ('lemon', 'Lemon'), ('carrot', 'Carrot'), ('mocha', 'Mocha'), ('ube', 'Ube'), ('pandan', 'Pandan')], max_length=50)),
                ('size', models.CharField(choices=[('4inch', '4 inch (2-4 servings)'), ('6inch', '6 inch (6-8 servings)'), ('8inch', '8 inch (10-12 servings)'), ('10inch', '10 inch (20-25 servings)'), ('12inch', '12 inch (30-35 servings)'), ('sheet', 'Sheet Cake (50+ servings)')], max_length=20)),
                ('baseprice', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(blank=True)),
                ('is_available', models.BooleanField(default=True)),
            ],
            options={'ordering': ['caketype', 'flavor']},
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('staffID', models.AutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('name', models.CharField(max_length=200)),
                ('number', models.CharField(max_length=20)),
                ('role', models.CharField(choices=[('baker', 'Baker'), ('decorator', 'Cake Decorator'), ('manager', 'Manager'), ('cashier', 'Cashier'), ('delivery', 'Delivery')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'Staff'},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('orderID', models.AutoField(primary_key=True, serialize=False)),
                ('customerID', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='orders.customer')),
                ('cakeID', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='orders.cake')),
                ('orderdate', models.DateField(auto_now_add=True)),
                ('pickupdate', models.DateField()),
                ('orderstatus', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('in_production', 'In Production'), ('ready', 'Ready for Pickup'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('totalprice', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ['-orderdate']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('orderitemID', models.AutoField(primary_key=True, serialize=False)),
                ('orderID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='orders.order')),
                ('cakeID', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='orders.cake')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('design_notes', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('paymentID', models.AutoField(primary_key=True, serialize=False)),
                ('orderID', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='orders.order')),
                ('paymentdate', models.DateField(auto_now_add=True)),
                ('paymentmethod', models.CharField(choices=[('cash', 'Cash'), ('gcash', 'GCash'), ('bank_transfer', 'Bank Transfer'), ('card', 'Credit/Debit Card')], max_length=20)),
                ('paymentstatus', models.CharField(choices=[('pending', 'Pending'), ('partial', 'Partial Payment'), ('paid', 'Fully Paid'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reference_number', models.CharField(blank=True, max_length=100)),
            ],
            options={'ordering': ['-paymentdate']},
        ),
        migrations.CreateModel(
            name='ProductionTask',
            fields=[
                ('taskID', models.AutoField(primary_key=True, serialize=False)),
                ('orderitemID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='orders.orderitem')),
                ('staffID', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='orders.staff')),
                ('task_type', models.CharField(choices=[('baking', 'Baking'), ('decorating', 'Decorating'), ('fondant', 'Fondant Work'), ('assembly', 'Assembly'), ('packaging', 'Packaging'), ('quality_check', 'Quality Check')], max_length=20)),
                ('productiondate', models.DateField()),
                ('starttime', models.TimeField()),
                ('endtime', models.TimeField()),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('delayed', 'Delayed')], default='scheduled', max_length=20)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ['productiondate', 'starttime']},
        ),
    ]
