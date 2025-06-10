from django.db import models

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50)

    def __str__(self):
        return self.category_name

    class Meta:
        db_table = "Category"

class Product(models.Model):
    product_name = models.CharField(max_length=50)
    price = models.FloatField(default=200)
    size = models.CharField(max_length=30)
    description = models.CharField(max_length=1000)
    image = models.ImageField(upload_to='product_images/')
    #image1 = models.ImageField(upload_to="images",default="abc.jpg").... If want more than more images for 1 product
    category = models.ForeignKey(Category,on_delete=models.CASCADE)

     # New fields for deals support
    discount_price = models.FloatField(null=True, blank=True)
    discount_percent = models.IntegerField(null=True, blank=True)
    is_deal = models.BooleanField(default=False)  # To mark deal items
    show_on_homepage = models.BooleanField(default=True)
    show_on_carousel = models.BooleanField(default=False)

    def __str__(self):
        return self.product_name

    class Meta:
        db_table = "Product"


class RazorpayPayment(models.Model):
    order_id = models.CharField(max_length=100)
    #payment_id = models.CharField(max_length=100, null=True, blank=True)
    #signature = models.TextField(null=True, blank=True)
    amount = models.FloatField()
    status = models.CharField(max_length=20, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_id}"
    
class CarouselItem(models.Model):
    title = models.CharField(max_length=100,blank=True, null=True)
    caption = models.TextField(blank=True,null=True)
    image = models.ImageField(upload_to='carousel/')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or "Carousel Image"


        
