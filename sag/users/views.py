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
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            
            # Check if email is already taken
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, "A user with this email already exists.")
                return render(request, 'users/register_user.html', {'form': form})

            # Create User: We use email as the technical username to satisfy uniqueness
            user = User.objects.create_user(
                username=email, 
                email=email, 
                password=password
            )

            # Update UserProfile: This is where the non-unique Name is stored
            profile = user.userprofile
            profile.name = name
            profile.father_name = form.cleaned_data.get('father_name', '')
            profile.nationality = form.cleaned_data.get('nationality', '')
            profile.phone = form.cleaned_data.get('phone', '')
            profile.role = form.cleaned_data.get('role', '')
            if form.cleaned_data.get('profile_picture'):
                profile.profile_picture = form.cleaned_data.get('profile_picture')
            
            profile.status = 'active'
            profile.save()

            messages.success(request, f"User {name} registered successfully!")
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




from .models import Team
from .forms import TeamForm

# # Helper to check if user is HR
# def is_hr(user):
#     return hasattr(user, 'userprofile') and user.userprofile.role == constants.ROLE_HR

# @user_passes_test(is_hr)
def team_list(request):
    teams = Team.objects.all()
    return render(request, 'users/team_list.html', {'teams': teams})

# @user_passes_test(is_hr)
def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'users/team_form.html', {'form': form, 'title': 'Create Team'})

# @user_passes_test(is_hr)
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'users/team_form.html', {'form': form, 'title': 'Update Team'})

# @user_passes_test(is_hr)
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        team.delete()
        return redirect('team_list')
    return render(request, 'users/team_confirm_delete.html', {'team': team})

def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    # Fetch all members associated with this team
    members = team.members.all()
    return render(request, 'users/team_detail.html', {
        'team': team,
        'members': members
    })

@login_required
@role_required(['admin','hr'])
def teams_base(request):
    return render(request, 'users/base_teams.html')
@login_required
@role_required(['admin','hr'])
def user_base(request):
    return render(request, 'users/base_user_management.html')



# views.py
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

def test_email_sending(request):
    """
    A manual trigger to test if SMTP settings are correct.
    """
    # 1. Define dummy data
    test_receiver = "habibazeem658@gmail.com" # <--- PUT YOUR EMAIL HERE
    dummy_task_name = "Test Factory Machine Maintenance"
    dummy_manager = "Admin Test User"
    dummy_deadline = "2025-12-31"

    subject = "FACTORY SYSTEM TEST: New Task Assigned"
    message = (
        f"This is a dummy test email.\n\n"
        f"Task: {dummy_task_name}\n"
        f"Assigned By: {dummy_manager}\n"
        f"Deadline: {dummy_deadline}\n\n"
        f"If you see this, your SMTP settings are working perfectly!"
    )

    try:
        # 2. Attempt to send
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [test_receiver],
            fail_silently=False,
        )
        return HttpResponse(f"<h2>Success!</h2> Email sent to {test_receiver}. Check your inbox (and spam folder).")
    
    except Exception as e:
        # 3. Catch and display errors
        return HttpResponse(f"<h2>Failed!</h2> Error details: <br><code>{str(e)}</code>")