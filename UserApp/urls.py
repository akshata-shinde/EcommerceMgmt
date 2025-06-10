from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('ShowProducts/<id>',views.ShowProducts),
    path('ViewDetails/<id>',views.ViewDetails, name='ViewDetails'),
    path('Login',views.Login),
    path('SignUp',views.SignUp),
    path('SignOut',views.SignOut),
    path('addToCart',views.addToCart),
    path('showCartItems',views.showCartItems),
    path('AutoPayment',views.AutoPayment),
    path('PurchaseHistory/',views.PurchaseHistory),
    path('payment-success/', views.PaymentSuccess), # given in Razorpay handler in autoapyment.html
    path('order-success/', views.order_success),
    path('contactus',views.contactus),
    path('deals',views.deals),
    path('aboutus',views.aboutus),
    path('SearchProduct', views.SearchProduct),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    
]
