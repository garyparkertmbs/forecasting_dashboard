from functools import wraps
from django.http import HttpResponseRedirect
from dashApp.models import *
from django.shortcuts import render,redirect

# def login_required(funct)
def subscribers_only(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
        user = StripeCustomer.objects.get(user=request.user)
        print("user",user,user.is_subscribed)
        if user.is_subscribed:
            print(request, args, kwargs)
            return function(request, *args, **kwargs)  
        else:
            return HttpResponseRedirect('/subscription/')

  return wrap
