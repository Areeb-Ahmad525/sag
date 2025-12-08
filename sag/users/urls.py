from django.urls import path
from . import views

urlpatterns = [
    # path('',views.login_view,name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_user, name='register_user'),
    path('list/', views.user_list, name='user_list'),
    path('toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
]
