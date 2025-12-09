from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def homePage(request):
    """Home page view"""
    return render(request, 'home.html')

@login_required(login_url='/accounts/login')
def dashboard_view(request):
    context = {
        'title': 'Dashboard',
    }
    return render(request, 'core/dashboard_content.html', context)

def services(request):
    """Services page view"""
    return render(request, 'services.html')

def about(request):
    """About page view"""
    return render(request, 'about.html')

def contact(request):
    """Contact page view with form handling"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        service = request.POST.get('service')
        message = request.POST.get('message')
        
        # Here you can add email sending logic or save to database
        # For now, we'll just show a success message
        
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        
        # You can add email sending code here like:
        # from django.core.mail import send_mail
        # send_mail(
        #     f'New Contact Form Submission from {name}',
        #     f'Name: {name}\nEmail: {email}\nPhone: {phone}\nService: {service}\nMessage: {message}',
        #     'from@example.com',
        #     ['info@saudaluminium.com'],
        #     fail_silently=False,
        # )
    
    return render(request, 'contact.html')

