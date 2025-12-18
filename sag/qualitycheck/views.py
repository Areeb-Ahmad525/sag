from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import QualityInspectionForm
from django.shortcuts import render
from .models import QualityInspection

@login_required
def inspection_list(request):
    inspections = QualityInspection.objects.all().order_by('-inspection_date', '-inspection_time')
    return render(request, 'qualitycheck/inspection_list.html', {'inspections': inspections})



@login_required
def create_inspection(request):
    if request.method == 'POST':
        form = QualityInspectionForm(request.POST)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.inspector = request.user  # QC Officer
            inspection.save()
            return redirect('inspection_list')
    else:
        form = QualityInspectionForm()

    return render(request, 'qualitycheck/create_inspection.html', {'form': form})

@login_required
def qualitycheck_base(request):
    return render(request, 'qualitycheck/base_qualitycheck.html')
