# procurement/urls.py
from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('', views.procurement_index, name='procurement_index'),

    # PR
    path('prs/', views.pr_list, name='pr_list'),
    path('prs/create/', views.pr_create, name='pr_create'),
    path('prs/<int:pr_id>/', views.pr_detail, name='pr_detail'),
    path('prs/<int:pr_id>/submit/', views.pr_submit, name='pr_submit'),
    path('prs/<int:pr_id>/approve/', views.pr_approve, name='pr_approve'),

    # Quotations
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/create/', views.quotation_create, name='quotation_create'),
    path('quotations/<int:q_id>/', views.quotation_detail, name='quotation_detail'),
    path('quotations/<int:q_id>/send/', views.quotation_send, name='quotation_send'),

    path('quotations/<int:q_id>/accept/', views.quotation_accept, name='quotation_accept'),

    # PO
    path('pos/', views.po_list, name='po_list'),
    path('pos/create/', views.po_create, name='po_create'),
    path('pos/<int:po_id>/', views.po_detail, name='po_detail'),
    path('pos/<int:po_id>/send/', views.po_send, name='po_send'),

    # GRN
    path('grns/', views.grn_list, name='grn_list'),
    path('grns/create/', views.grn_create, name='grn_create'),
    path('grns/<int:grn_id>/', views.grn_detail, name='grn_detail'),
    path('grns/<int:grn_id>/confirm/', views.grn_confirm, name='grn_confirm'),
]
