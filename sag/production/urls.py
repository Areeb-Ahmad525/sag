from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [

    # DASHBOARD
    path('', views.production_index, name='production_base'),

    # WORK ORDERS
    path('workorders/', views.wo_list, name='wo_list'),
    path('workorders/create/', views.wo_create, name='wo_create'),
    path('workorders/<int:wo_id>/', views.wo_detail, name='wo_detail'),
    path('workorders/<int:wo_id>/edit/', views.wo_update, name='wo_update'),
    path('workorders/<int:wo_id>/delete/', views.wo_delete, name='wo_delete'),

        # WORK ORDER STATUS
    path('workorders/<int:wo_id>/start/', views.wo_start, name='wo_start'),
    path('workorders/<int:wo_id>/complete/', views.wo_complete, name='wo_complete'),

    # TASKS
    path('workorders/<int:wo_id>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/start/', views.task_start, name='task_start'),
    path('tasks/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),

    path('tasks/', views.task_list, name='task_list'),


    # CONSUMPTION
    path(
        'workorders/<int:wo_id>/consumption/create/',
        views.consumption_create,
        name='consumption_create'
    ),
    path(
        'consumption/<int:consumption_id>/delete/',
        views.consumption_delete,
        name='consumption_delete'
    ),

    # OUTPUT
    path(
        'workorders/<int:wo_id>/output/create/',
        views.output_create,
        name='output_create'
    ),

    # WASTAGE
    path(
        'workorders/<int:wo_id>/wastage/create/',
        views.wastage_create,
        name='wastage_create'
    ),
]
