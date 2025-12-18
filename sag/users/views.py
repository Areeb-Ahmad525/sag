# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone

from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile, LoginActivity
from .decorators import role_required

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # may contain multiple IPs, the first is original client
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    """
    Accepts either email or username in the 'username' field thanks to custom backend.
    Blocks login for user.is_active == False.
    Logs LoginActivity entries for audit.
    """
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]

        if user is not None:
            if not user.is_active:
                # record failed attempt for inactive
                try:
                    LoginActivity.objects.create(user=user, ip_address=ip, user_agent=user_agent, status='failed')
                except Exception:
                    pass
                messages.error(request, "Your account is inactive. Contact admin.")
                return redirect('login')
            login(request, user)
            
            # ⭐ Force password change
            if user.userprofile.must_change_password:
                messages.warning(request, "You must change your password before accessing the system.")
                return redirect('change_password')

            try:
                LoginActivity.objects.create(user=user, ip_address=ip, user_agent=user_agent, status='success')
            except Exception:
                pass
            messages.success(request, 'Logged In Successfully')
            return redirect('dashboard')
        else:
            # attempt to attach the failed record to a matched user if possible
            matched_user = None
            try:
                matched_user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=username).first()
            except Exception:
                matched_user = None
            try:
                LoginActivity.objects.create(user=matched_user, ip_address=ip, user_agent=user_agent, status='failed')
            except Exception:
                pass
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    # record logout_time on last successful login activity for this user
    try:
        last_activity = LoginActivity.objects.filter(user=request.user, status='success').order_by('-login_time').first()
        if last_activity and not last_activity.logout_time:
            last_activity.logout_time = timezone.now()
            last_activity.save()
    except Exception:
        pass

    logout(request)
    messages.info(request, "You’ve been logged out.")
    return redirect('login')


def register_user(request):
    """
    Only HR/Admin can register new users. Uses email as username.
    """
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            father_name = form.cleaned_data.get('father_name', '')
            nationality = form.cleaned_data.get('nationality', '')
            phone = form.cleaned_data.get('phone', '')
            role = form.cleaned_data.get('role', '')
            picture = form.cleaned_data.get('profile_picture')

            # Prevent duplicate email/username
            if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
                messages.error(request, "A user with that email already exists.")
                return redirect('register_user')

            # Create User with username=email
            user = User.objects.create_user(username=email, email=email, password=password)
            user.save()

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.name = name
            profile.father_name = father_name
            profile.nationality = nationality
            profile.phone = phone
            profile.role = role
            if picture:
                profile.profile_picture = picture

            # Keep status mapping to Django's is_active
            profile.must_change_password = True
            profile.status = 'active'
            profile.save()
            user.is_active = True
            user.save()

            messages.success(request, "User registered successfully!")
            return redirect('user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register_user.html', {'form': form})

@login_required
def user_list(request):
    """
    List all user profiles for HR/Admin to view/manage.
    Non HR/Admin users can still view the list if allowed by business rules, but actions hidden in template.
    """
    users = UserProfile.objects.select_related('user').all()
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def toggle_user_status(request, user_id):
    """
    Toggle active/inactive status for a user profile.
    (This will also set User.is_active)
    Only HR/Admin should have link to this action in templates.
    """
    profile = get_object_or_404(UserProfile, user_id=user_id)
    profile.status = 'inactive' if profile.status == 'active' else 'active'
    profile.save()
    # sync Django User.is_active
    profile.user.is_active = True if profile.status == 'active' else False
    profile.user.save()
    messages.success(request, "User status updated!")
    return redirect('user_list')

@login_required
def edit_profile(request):
    """
    Allow logged-in users to edit their own profile (safe fields only).
    Role cannot be changed here.
    """
    profile = getattr(request.user, 'userprofile', None)
    if not profile:
        messages.error(request, "Profile not found.")
        return redirect('dashboard')

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('edit_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """
    Allow logged-in users to change their password via Django's PasswordChangeForm.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged-in after password change
            update_session_auth_hash(request, user)
            # ⭐ Mark password as changed
            profile = request.user.userprofile
            profile.must_change_password = False
            profile.save()
            messages.success(request, 'Your password was successfully updated!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})
