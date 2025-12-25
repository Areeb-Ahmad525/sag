from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from users.models import UserProfile
from users import constants
from .models import Attendance
from .forms import AttendanceSheetForm
from users.decorators import role_required
from django.db import models



ALLOWED_ROLES=['hr','admin']

@login_required
@role_required(ALLOWED_ROLES)
def attendance_list(request):
    date = request.GET.get("date")

    qs = Attendance.objects.all()

    if date:
        qs = qs.filter(date=date)

    records = (
        qs.values("date")
        .annotate(
            total_present=models.Count("id", filter=models.Q(status="present")),
            marked_time=models.Max("created_at")
        )
        .order_by("-date")
    )

    return render(request, "attendance/attendance_list.html", {
        "records": records,
        "selected_date": date
    })


@login_required
@role_required(ALLOWED_ROLES)
@require_http_methods(["GET", "POST"])
def mark_attendance(request):
    today = timezone.localdate()

    if Attendance.objects.filter(date=today).exists():
        messages.error(request, "Attendance for today has already been marked.")
        return redirect("attendance:attendance_list")

    employees = UserProfile.objects.exclude(
        role__in=[constants.ROLE_ADMIN, constants.ROLE_HR]
    ).filter(status="active")

    rows = []

    if request.method == "POST":
        for emp in employees:
            status = request.POST.get(f"status_{emp.id}")
            remarks = request.POST.get(f"remarks_{emp.id}", "")

            Attendance.objects.create(
                employee=emp,
                date=today,
                status=status,
                remarks=remarks,
                marked_by=request.user.userprofile
            )

        messages.success(request, "Attendance marked successfully.")
        return redirect("attendance:attendance_list")

    for emp in employees:
        rows.append(emp)

    return render(request, "attendance/attendance_sheet.html", {
        "employees": rows,
        "date": today
    })


@login_required
@role_required(ALLOWED_ROLES)
def attendance_detail(request, date):
    records = Attendance.objects.filter(date=date)
    return render(request, "attendance/attendance_detail.html", {
        "records": records,
        "date": date
    })


@login_required
@role_required(ALLOWED_ROLES)
def delete_attendance(request, date):
    records = Attendance.objects.filter(date=date)

    if not records or not records.first().is_editable():
        messages.error(request, "Attendance can no longer be deleted.")
        return redirect("attendance:attendance_list")

    records.delete()
    messages.success(request, "Attendance deleted successfully.")
    return redirect("attendance:attendance_list")


@login_required
@role_required(ALLOWED_ROLES)
def attendance_report(request):
    month = request.GET.get("month")
    report = []

    employees = UserProfile.objects.exclude(
        role__in=[constants.ROLE_ADMIN, constants.ROLE_HR]
    ).select_related("user")

    if month:
        year, m = month.split("-")
        qs = Attendance.objects.filter(
            date__year=year,
            date__month=m
        )

        for emp in employees:
            report.append({
                "employee": emp,
                "present": qs.filter(employee=emp, status="present").count(),
                "absent": qs.filter(employee=emp, status="absent").count(),
            })

    return render(request, "attendance/attendance_report.html", {
        "report": report,
        "month": month
    })



@login_required
@role_required(ALLOWED_ROLES)
@require_http_methods(["GET", "POST"])
def attendance_edit(request, date):
    """
    Edit attendance for a given date. 
    Only editable if within allowed time (6 hours).
    """
    # Get existing attendance records for that date
    records = Attendance.objects.filter(date=date).select_related("employee")

    if not records.exists():
        messages.error(request, "No attendance found for this date.")
        return redirect("attendance:attendance_list")

    # Check if editable
    if not records.first().is_editable():
        messages.error(request, "Attendance can no longer be edited.")
        return redirect("attendance:attendance_list")

    # Get all active employees excluding HR/Admin
    employees = UserProfile.objects.exclude(
        role__in=[constants.ROLE_ADMIN, constants.ROLE_HR]
    ).filter(status="active")

    # Map existing attendance by employee id
    existing_data = {
        r.employee.id: {
            "status": r.status,
            "remarks": r.remarks
        }
        for r in records
    }

    if request.method == "POST":
        # Use transaction to update safely
        with transaction.atomic():
            for emp in employees:
                status = request.POST.get(f"status_{emp.id}")
                remarks = request.POST.get(f"remarks_{emp.id}", "")

                # Update existing record or create if missing (safety)
                Attendance.objects.update_or_create(
                    employee=emp,
                    date=date,
                    defaults={
                        "status": status,
                        "remarks": remarks,
                        "marked_by": request.user.userprofile
                    }
                )

        messages.success(request, f"Attendance for {date} updated successfully.")
        return redirect("attendance:attendance_list")

    return render(request, "attendance/attendance_sheet.html", {
        "employees": employees,
        "date": date,
        "existing_data": existing_data,
        "is_edit": True,  # flag to adjust template buttons
    })
