from django.urls import path
from . import views

urlpatterns = [
    # path('',views.login_view,name='login'),
    path('', views.user_base, name='user_base'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_user, name='register_user'),
    path('list/', views.user_list, name='user_list'),
    path('toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),


    path('teams/', views.teams_base, name='teams_base'),
    path('teams-list/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/update/<int:pk>/', views.team_update, name='team_update'),
    path('teams/delete/<int:pk>/', views.team_delete, name='team_delete'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
]
