from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/add/', views.quotation_create, name='quotation_create'),
    path('quotations/<int:pk>/edit/', views.quotation_update, name='quotation_update'),
    path('quotations/<int:pk>/delete/', views.quotation_delete, name='quotation_delete'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/add/', views.order_create, name='order_create'),
    path('orders/<int:pk>/edit/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

]

