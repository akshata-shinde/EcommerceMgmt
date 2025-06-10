import razorpay
import json
import time
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render,redirect,get_object_or_404
from AdminApp.models import Category,Product,RazorpayPayment,CarouselItem
from UserApp.models import UserInfo,MyCart,OrderMaster,OrderStatus
from django.http import HttpResponse
from django.contrib import messages
from django.template.context_processors import csrf
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import traceback
from django.contrib.auth import login
from django.db.models import Q
import threading



# Create your views here.




'''def home(request):
    cats = Category.objects.all()
    products = Product.objects.filter(show_on_homepage=True)
    carousel_items = CarouselItem.objects.all()  # Only shown in carousel
    return render(request, "master.html", {
        "cats": cats,
        "products": products,
        "carousel_items": carousel_items,
    })

def home(request):
    cats = Category.objects.all()
    products = Product.objects.filter(show_on_homepage=True)  # Only homepage products
    carousel_items = Product.objects.filter(show_on_carousel=True)  # Products in carousel
    return render(request, "master.html", {
        "cats": cats,
        "products": products,
        "carousel_items": carousel_items,
    }) '''

def home(request):
    cats = Category.objects.all()

    # Exclude products that are in any CarouselItem
    carousel_products = CarouselItem.objects.filter(product__isnull=False).values_list('product_id', flat=True)

    # Show only products marked for homepage, but not those used in carousel
    products = Product.objects.filter(show_on_homepage=True).exclude(id__in=carousel_products)

    carousel_items = CarouselItem.objects.filter(is_active=True)

    return render(request, "master.html", {
        "cats": cats,
        "products": products,
        "carousel_items": carousel_items,
    })




def ShowProducts(request,id):
    cats = Category.objects.all()
    products = Product.objects.filter(category = id)
    return render(request,"master.html",{"cats":cats, "products": products})

def ViewDetails(request,id):
    cats = Category.objects.all()
    product = Product.objects.get(id=id)
    return render(request,"ViewDetails.html",{"cats":cats, "product": product})

def addToCart(request):
    if("uname" in request.session):
        #get your info
        user = UserInfo.objects.get(username = request.session["uname"])
        #getting prod info
        product_id = request.POST["pid"]
        product = Product.objects.get(id=product_id)
        qty = request.POST["qty"]
        try:
            item = MyCart.objects.get(user=user,product=product)
        except:
            cart = MyCart()
            cart.user = user
            cart.product = product
            cart.qty = qty
            cart.save()
            messages.info(request,"Product Successfully Added in Cart")
            #return redirect(showCartItems)
        else:
            #return HttpResponse("Already in Cart")
            messages.info(request,"Product Already in Cart")
        return redirect(showCartItems)
    else:
        return redirect(Login)

def showCartItems(request):
    cats = Category.objects.all()
    user = UserInfo.objects.get(username=request.session["uname"])

    if(request.method == "GET"):
        items = MyCart.objects.filter(user=user)
        total = 0
        for item in items:
            total += item.qty*item.product.price
        request.session["total"] = total
        return render(request,"showAllCartItems.html",{"items":items,"cats":cats,"total":total})
    else:
        product_id = request.POST["product_id"]
        item = MyCart.objects.get(id=product_id,user=user)
        action = request.POST["action"]
        if(action == "remove"):
            item.delete()
        else:
            qty = request.POST["qty"]
            item.qty = qty
            item.save()
        return redirect(showCartItems)

def contactus(request):
    cats = Category.objects.all()
    return render(request,"contactus.html",{'cats':cats})


'''def deals(request):
    query = request.GET.get('q', '')
    deal_products = Product.objects.filter(is_deal=True)

    if query:
        deal_products = deal_products.filter(product_name__icontains=query)

    return render(request, "deals.html", {
        "products": deal_products,
        "query": query,
    })'''

def deals(request):
    deals_products = Product.objects.filter(is_deal=True)  # Deals page products
    return render(request, "deals.html", {
        "products": deals_products,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


def create_razorpay_order(amount_in_rupees):
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_paise = int(amount_in_rupees * 100)
        payment = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1"
        })
        return payment
    except Exception as e:
        print("Error in create_razorpay_order:", str(e))
        raise

def AutoPayment(request):
    try:
        uname = request.session.get("uname")
        if not uname:
            return HttpResponse("User not logged in. Please login first.")

        try:
            user = UserInfo.objects.get(username=uname)
        except UserInfo.DoesNotExist:
            return HttpResponse("User not found.")

        cart_items = MyCart.objects.filter(user=user)
        if not cart_items.exists():
            return HttpResponse("Your cart is empty! Please add products first.")

        amount = sum(item.product.price * item.qty for item in cart_items)
        amount = round(amount, 2)

        if amount < 1:
            return HttpResponse("Amount must be at least ₹1 to proceed with payment.")

        try:
            payment = create_razorpay_order(amount)
            print("RAZORPAY PAYMENT OBJECT:", payment)
        except Exception as e:
            print("Razorpay error:", str(e))
            return HttpResponse(f"Failed to create Razorpay order: {str(e)}")

        RazorpayPayment.objects.create(
            order_id=payment['id'],
            amount=amount,
            status='created'
        )

        csrf_token = get_token(request)

        context = {
            'payment': payment,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'csrf_token': csrf_token,
            'total_amount': amount
        }

        return render(request, 'AutoPayment.html', context)
    
    except Exception as ex:
        print("Unhandled error in AutoPayment view:", str(ex))
        return HttpResponse("Error while processing order.")


def PurchaseHistory(request):
    uname = request.session.get("uname")
    if not uname:
        return redirect('/Login')
    
    try:
        user = UserInfo.objects.get(username=uname)
    except UserInfo.DoesNotExist:
        return redirect('/Login')
    
    history = OrderMaster.objects.filter(user=user).order_by('-purchase_date')
    
    return render(request, 'PurchaseHistory.html', {'history': history})


@csrf_exempt
def PaymentSuccess(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_order_id = data.get("razorpay_order_id")

            if not razorpay_payment_id or not razorpay_order_id:
                return JsonResponse({'status': 'failed', 'reason': 'Missing payment or order ID'})

            uname = request.session.get("uname")
            if not uname:
                return JsonResponse({'status': 'failed', 'reason': 'No user session'})

            user = UserInfo.objects.get(username=uname)
            cart_items = MyCart.objects.filter(user=user)

            if not cart_items.exists():
                return JsonResponse({'status': 'failed', 'reason': 'Cart empty'})

            # Update RazorpayPayment record
            try:
                payment = RazorpayPayment.objects.get(order_id=razorpay_order_id)
                payment.status = 'paid'
                payment.save()
            except RazorpayPayment.DoesNotExist:
                print("RazorpayPayment record not found for order_id:", razorpay_order_id)

            # Create order and status records
            for item in cart_items:
                try:
                    order = OrderMaster.objects.create(
                        user=user,
                        product=item.product,
                        product_name=item.product.product_name,
                        price=item.product.price,
                        quantity=item.qty,
                        product_image=item.product.image,
                        razorpay_payment_id=razorpay_payment_id,
                        date_of_order=timezone.now()
                    )

                # ✅ Create tracking status for each order
                    OrderStatus.objects.create(
                        order=order,
                        current_status='placed',
                        estimated_delivery=datetime.now().date() + timedelta(days=5),
                        shipping_id=f"SHIP-{order.id}"
                    )

                except Exception as e:
                    print("Error creating order for item:", item.product.product_name)
                    print(traceback.format_exc())  # ✅ More useful
                    return JsonResponse({'status': 'failed', 'reason': f'Order creation error: {str(e)}'})

            # Clear cart
            cart_items.delete()

            return JsonResponse({'status': 'success'})

        except Exception as e:
            print("Error in PaymentSuccess:", str(e))
            return JsonResponse({'status': 'failed', 'reason': str(e)})

    else:
        return JsonResponse({'status': 'failed', 'reason': 'Invalid request method'})


def simulate_status_updates(orderstatus):
    delays = [5, 5, 5]  # delays in seconds between each status
    for delay in delays:
        time.sleep(delay)
        updated = orderstatus.advance_status()
        if not updated:
            break  # stop if already delivered or something goes wrong

# View triggered after successful payment
def generate_sequential_dates(base_date, steps_keys):
    dates = {}
    for i, key in enumerate(steps_keys):
        step_date = base_date + timedelta(days=i)
        formatted = step_date.strftime("%B %d, %Y, %I:%M %p").lower().replace("am", "a.m.").replace("pm", "p.m.")
        dates[key] = formatted
    return dates

def order_success(request): 
    payment_id = request.GET.get("payment_id")
    uname = request.session.get("uname")

    if not uname or not payment_id:
        return render(request, 'order_success.html', {'orders': []})

    orders = OrderMaster.objects.filter(user__username=uname, razorpay_payment_id=payment_id)
    enriched_orders = []

    statuses = ["placed", "dispatched", "out_for_delivery", "delivered"]

    for order in orders:
        try:
            orderstatus = order.orderstatus

            # Start tracking simulation if status is "placed"
            if orderstatus.current_status == 'placed':
                thread = threading.Thread(target=simulate_status_updates, args=(orderstatus,))
                thread.daemon = True
                thread.start()
            
            # Base date for sequential dates: use placed_at or fallback to now
            base_date = getattr(orderstatus, 'placed_at', None)
            if not base_date:
                base_date = datetime.now()

            step_keys = ["placed", "dispatched", "out_for_delivery", "delivered"]
            sequential_dates = generate_sequential_dates(base_date, step_keys)

            # Format estimated delivery nicely
            estimated_delivery_str = orderstatus.estimated_delivery.strftime("%B %d, %Y") if orderstatus.estimated_delivery else None


            steps = [
                {
                    "key": "placed",
                    "label": "Order Confirmed",
                    "date": sequential_dates.get("placed"),
                    "desc": None
                },
                {
                    "key": "dispatched",
                    "label": "Shipped",
                    "date": getattr(orderstatus, 'dispatched_at', None),
                    "desc": "Your item has left the warehouse."
                },
                {
                    "key": "out_for_delivery",
                    "label": "Out for Delivery",
                    "date": sequential_dates.get("dispatched"),
                    "desc": None
                },
                {
                    "key": "delivered",
                    "label": "Delivered",
                    "date": sequential_dates.get("delivered"),
                    "desc": f"Expected by {estimated_delivery_str}" if estimated_delivery_str else None
                }
                
            ]

            # Calculate completed steps based on current_status
            try:
                current_index = statuses.index(orderstatus.current_status)
            except ValueError:
                current_index = -1

            for step in steps:
                try:
                    step_index = statuses.index(step["key"])
                except ValueError:
                    step_index = -1
                step["is_completed"] = (step_index <= current_index)

            enriched_orders.append({
                "product_name": order.product_name,
                "product_image": order.product_image.url if order.product_image else None,
                "shipping_id": orderstatus.shipping_id,
                "estimated_delivery": estimated_delivery_str,
                "current_status": orderstatus.current_status,
                "steps": steps
            })

        except OrderStatus.DoesNotExist:
            continue

    return render(request, 'order_success.html', {'orders': enriched_orders})

def SignOut(request):
    #delete the session
    request.session.clear()
    return redirect(home)

def Login(request):
    message = ''
    
    if(request.method=="GET"):
        return render(request,"Login.html")
    else:
        uname = request.POST["uname"]
        pwd = request.POST["pwd"]

        if not uname or not pwd:
            message = "Please Enter Both Username and Password!!"
            return render(request, "Login.html", {"message": message})
        try:
            #If user is already present
            user = UserInfo.objects.get(username=uname,password=pwd)            
        except:
            #Login fail
           message = "Invalid Credentials, Please Try Again!!"
           return render(request,"Login.html",{"message":message})
           #messages.info(request,"Login Successfully!!")
        else:
            #if login successful then create a session for that user
            request.session["uname"]=uname
            return render(request, "Login.html", {"message": "Login Successful!!"})

def SignUp(request):
    if request.method == "GET":
        return render(request, "SignUp.html")
    else:
        uname = request.POST.get("uname")
        pwd = request.POST.get("pwd")

        if not uname or not pwd:
            message = "Please Enter Both Username and Password!!"
            return render(request, "Login.html", {"message": message})

        try:
            # If user already exists
            UserInfo.objects.get(username=uname)
            message = "User Already Exist!!"
            return render(request, "SignUp.html", {"message": message})
        except UserInfo.DoesNotExist:
            # Create user only once
            user = UserInfo(username=uname, password=pwd)
            user.save()
            return render(request, "SignUp.html", {"message": "SignUp Successful!!"})

            
'''def deals_view(request):
    products = Product.objects.all()
    return render(request, 'deals.html', {'products': products})'''


def aboutus(request):
    return render(request,"aboutus.html")


def SearchProduct(request):
    query = request.GET.get('q')
    products = []

    if query:
        products = Product.objects.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__category_name__icontains=query)
        )

    return render(request, 'SearchProduct.html', {'products': products, 'query': query})



