from django.urls import path
from . import views

urlpatterns = [
    path('', views.qualitycheck_base, name='qualitycheck_base'),
    path('inspection/create/', views.create_inspection, name='create_inspection'),
    path('inspection/list/', views.inspection_list, name='inspection_list'),
]
