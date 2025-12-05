from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
from .models import UserProfile
from .decorators import role_required




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
@login_required
@role_required(['hr','admin']) #to give access to only specific role
def register_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            father_name = form.cleaned_data['father_name']
            nationality = form.cleaned_data['nationality']
            phone = form.cleaned_data['phone']
            role = form.cleaned_data['role']
            picture = form.cleaned_data.get('profile_picture')

            # Create User
            user = User.objects.create_user(username=name, email=email, password=password)

            # Create or get UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.name = name
            profile.father_name = father_name
            profile.nationality = nationality
            profile.phone = phone
            profile.role = role
            if picture:
                profile.profile_picture = picture
            profile.save()

            messages.success(request, "User registered successfully!")
            return redirect('user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register_user.html', {'form': form})

@login_required
def user_list(request):
    users = UserProfile.objects.all()
    return render(request, 'users/user_list.html', {'users': users})



@login_required
def toggle_user_status(request, user_id):
    profile = get_object_or_404(UserProfile, user_id=user_id)
    profile.status = 'inactive' if profile.status == 'active' else 'active'
    profile.save()
    # also toggle User.is_active
    profile.user.is_active = True if profile.status == 'active' else False
    profile.user.save()
    messages.success(request, "User status updated!")
    return redirect('user_list')