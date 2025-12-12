from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.production_index, name='production_base'),
    path('workorders/', views.wo_list, name='wo_list'),
    path('workorders/create/', views.wo_create, name='wo_create'),
    path('workorders/<int:wo_id>/', views.wo_detail, name='wo_detail'),
    path('workorders/<int:wo_id>/start/', views.wo_start, name='wo_start'),
    path('workorders/<int:wo_id>/complete/', views.wo_complete, name='wo_complete'),
]
