from django.contrib import admin
from . models import Category,Product,CarouselItem

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id","category_name")

class ProductAdmin(admin.ModelAdmin):
    list_display = ("id","product_name","price","size","description","image","category","is_deal","show_on_homepage","show_on_carousel")
    list_editable = ('show_on_carousel', 'is_deal', 'show_on_homepage')

class CarouselItemAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)




admin.site.register(Category,CategoryAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(CarouselItem,CarouselItemAdmin)
#admin.site.register(Payment,PaymentAdmin)




