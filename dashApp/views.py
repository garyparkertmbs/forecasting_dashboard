from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from dashApp.models import *
from dashApp.decorators import subscribers_only

import stripe


def handler404(request, exception, template_name="404.html"):
    response = render(request, template_name)
    response.status_code = 404
    return response

def handler500(request, *args, **argv):
    return render(request, '500.html', status=500) 

# Create your views here.
def home(request):
    """ home() will be render landing home page.

    Returns:
       ["home.html] 

    """
    print("home page......")    
    return render(request, 'home.html')

@csrf_exempt
@login_required(login_url='/login/')      
@subscribers_only
def dashboard(request, template_name="dashboard.html", *args):
    """ dashboard() will be render dashboard of forcasting.

    Returns:
       ["dashboard.html] 

    """
    print("dashboard......")    
    return render(request, template_name='dashboard.html')

@csrf_exempt
def handleSignUp(request):
    """handleSignUp() will register user.

    Requirements:
        [1]: email-ID should be unique.
        [2]: length of password sholud be greater than 5.
        [3]: password and confirm_password should be same.

    Returns:
        [REQUEST-METHOD : POST] : [IF passes all requirements - "login.html"]
                                  [ELSE - "home.html"]
        [REQUEST-METHOD : GET] : [returns "home.html"]
    """ 
    if request.method == 'POST':
        print("request.POST", request.POST)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        try:
            if User.objects.filter(email=email) != User.objects.filter(email=email).exists(): 
                if len(password) < 5:
                    messages.error(request,"Password too much short")
                    return redirect('signup')
                
                if password != confirm_password:
                    messages.error(request,"Passwords do not match")
                    return redirect('signup')
                    
                myuser = User.objects.create_user(username=username,email=email,password=password)
                myuser.save()
                messages.success(request,"You have successfully Registered")
                print("Registerd..")
                return redirect('login')

        except:
            try:
                if User.objects.filter(email=email).exists():
                    messages.error(request,"Email exists Please Try other Email Address")

                elif User.objects.filter(username=username).exists():
                    messages.error(request,"Username exists Please Try another Username")
                return render(request,'signup.html')
            except:
                pass

        return redirect('home')
    

    return render(request, "signup.html")

@csrf_exempt
def handleLogIn(request):
    """handleLogIn() will authenticate user and log-in user to dashboard.

    Returns:
        [REQUEST-METHOD: POST] : [IF logIn done successfully - ("subscription.html" or "dashboard.html" -> depends on subscription)] 
                                 [ELSE display error message]
        [REQUEST-METHOD: GET] : [return "login.html"]

    """
    if request.method == 'POST':
        print("request.POST", request.POST)
        lemail = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = authenticate(username=lemail, password=password)
            if user is not None:
                login(request, user)
                request.session['user'] = lemail
                messages.info(request, f"You are now logged in as {lemail}.")
                print("logged in..")
                is_subscription = StripeCustomer.objects.get(user=user).is_subscribed
                print("is_subscription", is_subscription)
                if is_subscription:
                    return render(request, 'dashboard.html')
                else:
                    return redirect('subscription')
            else:
                messages.error(request,"Invalid username or password")
        except:
            messages.error(request, "Unable to logIn")

    return render(request, "login.html")   

def handlelogout(request):
    """handlelogout() will log out logged-in user.

    Returns:
        ["login.html"]: [successfully log-out]
        ["hime.html]: [unable to log-out]

    """
    try:
        logout(request)
        return redirect("login")
    except:
        messages.error("Unable to logout")
        return redirect("home")

def set_subscription(user):
    try:
        subscriber = StripeCustomer.objects.get(user=user)
        if subscriber:
            subscriber.is_subscribed = True
            subscriber.save()
            print("subscriber", subscriber.is_subscribed)
    except:
        print(f"unable to set is_subscribed for {user}")

@csrf_exempt
@login_required(login_url='/login/')
def stripe_config(request):
    """stripe_config() will handle the AJAX request.

    Returns:
        [JsonResponse]: json of STRIPE_PUBLISHABLE_KEY

    """
    if request.method == "GET":
        stripe_config = {"publicKey": settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=True)

@csrf_exempt
@login_required(login_url='/login/')
def create_checkout_session(request):
    """create_checkout_session() will send AJAX request to the server to generate a new Checkout Session ID.

    Returns:
        [IF payment success : "success.html"]
        [ELSE payment canceled : "cancel.html"]

    """
    if request.method == "GET":
        domain_url = "http://localhost:8000/"
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "cancel/",
                payment_method_types= ["card"],
                mode = "subscription",
                line_items=[
                    {
                        "price": 'price_1M2pexSIZVPMggpPjmxBWpqF',
                        "quantity": 1,
                    }
                ]
            )

            # set is_subscriptions field of user
            set_subscription(request.user)

            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            return JsonResponse({"error": str(e)})

@login_required(login_url='/login/')
def success(request):
    """success() will render on successfull subscription-payment.
    """
    return render(request, "success.html")

@login_required(login_url='/login/')
def cancel(request):
    """cancel() will render on cancellation of subscription-payment.
    """
    return render(request, "cancel.html")            

def handleSubscription(request):
    """cancel() will render pricing plans of all subscriptions.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    context = {"plan": {"name" : "Enterprise Plan", "price": 90.00}}
    return render(request, "subscription.html", context=context)    