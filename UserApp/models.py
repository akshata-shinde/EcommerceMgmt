from django.db import models
#from .models import Product
from AdminApp.models import Product
from datetime import datetime
from django.utils import timezone


# Create your models here.

class UserInfo(models.Model):
    username = models.CharField(max_length=25, primary_key=True)
    password = models.CharField(max_length=25)
    

    class Meta:
        db_table = "UserInfo"



class MyCart(models.Model):
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)

    class Meta:
        db_table = "MyCart"

class OrderMaster(models.Model):
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    date_of_order = models.DateField(default = datetime.now) 
    amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    details = models.CharField(max_length=200, blank=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    product_image = models.ImageField(upload_to='images/', blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically calculate amount on save
        self.amount = self.price * self.quantity
        self.details = f"{self.product_name} x {self.quantity}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = "OrderMaster"

class OrderStatus(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('dispatched', 'Dispatched'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]

    order = models.OneToOneField(OrderMaster, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    shipping_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    placed_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Status of order {self.order.id}: {self.get_current_status_display()}"

    class Meta:
        db_table = "OrderStatus"

    def get_next_status(self):
        flow = ['placed', 'dispatched', 'out_for_delivery', 'delivered']
        try:
            idx = flow.index(self.current_status)
            if idx < len(flow) - 1:
                return flow[idx + 1]
        except ValueError:
            return None
        return None

    def advance_status(self):
        next_status = self.get_next_status()
        if next_status:
            self.current_status = next_status
            self.updated_at = timezone.now()

            # Update the respective timestamp field
            now = timezone.now()
            if next_status == 'dispatched':
                self.dispatched_at = now
            elif next_status == 'out_for_delivery':
                self.out_for_delivery_at = now
            elif next_status == 'delivered':
                self.delivered_at = now

            self.save(update_fields=['current_status', 'updated_at', 'dispatched_at', 'out_for_delivery_at', 'delivered_at'])
            return True
        return False


