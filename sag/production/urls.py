from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [

    # Dashboard
    path('', views.production_index, name='production_base'),

    # Order detail (click card)
    path('order/<int:pk>/', views.production_order_detail, name='order_detail'),
    
    path('order/<int:pk>/request-inventory/',views.request_inventory,name='request_inventory'),
    
    path('order/<int:pk>/start-production/',views.start_production,name='start_production'),
    
    path('order/<int:pk>/complete/',views.complete_production,name='complete_production'),
    
    path('order/<int:order_id>/add-task/',views.add_production_task,name='add_task'),
    
    
     path('task/<int:task_id>/start/',views.start_task,name='start_task'),

    path('task/<int:task_id>/complete/',views.complete_task,name='complete_task'),

    path('task/<int:task_id>/edit/',views.edit_task,name='edit_task'),

    
]
