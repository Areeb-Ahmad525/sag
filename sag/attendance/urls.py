from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_list, name="attendance_list"),
    path("mark/", views.mark_attendance, name="mark"),
    path("report/", views.attendance_report, name="report"),  # ✅ STATIC FIRST
    path("<date>/", views.attendance_detail, name="detail"),
    path("<date>/delete", views.delete_attendance, name="delete_attendance"),
    path("edit/<str:date>/", views.attendance_edit, name="edit"),

]

