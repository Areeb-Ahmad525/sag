from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def login_view(request):
    if request.method == "POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            messages.success(request,'Logged In Successfully')
            return redirect('dashboard')
        # now it will navigate to main dashboard after successful login
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')
        

@login_required
def logout_view(request):
    logout(request)
    messages.info(request,'"You’ve been logged out.')
    return redirect('login')
        
