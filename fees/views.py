from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .forms import LoginForm, SecurityAnswerForm, StudentForm, ClassFeeForm, FeeRecordForm, FeePaymentForm, CustomUserCreationForm, CustomUserUpdateForm, GroupForm
from .models import FeePayment, FeeRecord, Student, ClassFee, CustomUser
from django.db.models import Sum
from datetime import datetime, date, timedelta
import csv
from .utils.reports_pdf import generate_payment_receipt
import json
from django.apps import apps
from django.contrib.auth.models import Group


def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('fees:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'fees/login.html')
    return render(request, 'fees/login.html')


def logout_view(request):
    logout(request)
    return redirect('fees:login')


def forgot_password(request):
    step = 1
    question = None
    if request.method == 'POST':
        if 'username' in request.POST and 'answer' not in request.POST and 'new_password' not in request.POST:
            username = request.POST.get('username')
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found')
                return redirect('fees:forgot_password')
            if not user.security_question:
                messages.error(request, 'No security question set for this user.')
                return redirect('fees:forgot_password')
            request.session['pw_reset_user'] = user.username
            question = dict(CustomUser._meta.get_field('security_question').choices).get(user.security_question)
            step = 2
        elif 'answer' in request.POST and 'new_password' not in request.POST:
            answer = request.POST.get('answer')
            uname = request.session.get('pw_reset_user')
            if not uname:
                messages.error(request, 'Session expired. Please start again.')
                return redirect('fees:forgot_password')
            user = CustomUser.objects.get(username=uname)
            question = dict(CustomUser._meta.get_field('security_question').choices).get(user.security_question)
            if user.check_security_answer(answer):
                step = 3
            else:
                messages.error(request, 'Incorrect answer')
                step = 2
        elif 'new_password' in request.POST:
            pwd = request.POST.get('new_password')
            pwd2 = request.POST.get('confirm_password')
            uname = request.session.get('pw_reset_user')
            if not uname:
                messages.error(request, 'Session expired. Please start again.')
                return redirect('fees:forgot_password')
            if not pwd or pwd != pwd2:
                messages.error(request, 'Passwords do not match')
                step = 3
            elif len(pwd) < 8:
                messages.error(request, 'Password must be at least 8 characters')
                step = 3
            else:
                user = CustomUser.objects.get(username=uname)
                user.set_password(pwd)
                user.save()
                try:
                    del request.session['pw_reset_user']
                except KeyError:
                    pass
                messages.success(request, 'Password reset successful. Please login.')
                return redirect('fees:login')
    return render(request, 'fees/forgot_password.html', {'step': step, 'question': question})


@login_required
def dashboard(request):
    total_students = Student.objects.count()
    current_month_str = datetime.now().strftime('%B %Y')
    
    collected = FeePayment.objects.filter(date__month=datetime.now().month, date__year=datetime.now().year).aggregate(total=Sum('amount'))['total'] or 0
    
    # ISSUE 2 Fix: Count of students with pending_amount > 0 for this month
    active_students = Student.objects.filter(is_active=True)
    pending_count = 0
    records = {r.student_id: r for r in FeeRecord.objects.filter(month=current_month_str)}
    for student in active_students:
        record = records.get(student.id)
        if record:
            if record.pending_amount > 0:
                pending_count += 1
        else:
            # No record for current month means it's pending
            pending_count += 1
    
    total_expected = 0
    class_fees = {cf.student_class: cf.fee_amount for cf in ClassFee.objects.all()}
    for student in Student.objects.all():
        total_expected += float(class_fees.get(student.student_class, student.total_fees))
    
    collection_rate = 0
    if total_expected > 0:
        collection_rate = int((float(collected) / float(total_expected)) * 100)

    chart_labels = []
    chart_data = []
    for i in range(5, -1, -1):
        target_date = datetime.now() - timedelta(days=i*30)
        month_label = target_date.strftime('%b')
        chart_labels.append(month_label)
        month_revenue = FeePayment.objects.filter(date__month=target_date.month, date__year=target_date.year).aggregate(total=Sum('amount'))['total'] or 0
        chart_data.append(float(month_revenue))

    recent_payments = FeePayment.objects.select_related('student').order_by('-date')[:10]
    
    return render(request, 'fees/dashboard.html', {
        'total_students': total_students,
        'collected': collected,
        'pending': pending_count,
        'collection_rate': collection_rate,
        'recent_payments': recent_payments,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
    })


@login_required
def manage_list(request, model_name):
    model_map = {
        'student': (Student, ['name', 'roll_no', 'student_class', 'is_active'], 'Students'),
        'classfee': (ClassFee, ['student_class', 'fee_amount'], 'Class Fees'),
        'feepayment': (FeePayment, ['student', 'amount', 'payment_mode', 'date'], 'Fee Payments'),
        'feerecord': (FeeRecord, ['student', 'month', 'status', 'paid_amount', 'pending_amount'], 'Fee Records'),
        'customuser': (CustomUser, ['username', 'email', 'is_staff', 'is_active'], 'Users'),
        'group': (Group, ['name'], 'Groups'),
    }

    if model_name not in model_map:
        return redirect('fees:dashboard')
    
    model, fields, title = model_map[model_name]

    # ADMIN-ONLY Check for Users and Groups
    if model_name in ['customuser', 'group'] and not request.user.is_superuser:
        messages.error(request, "Access Denied: Admin only.")
        return redirect('fees:dashboard')

    # Permission Check: View
    perm_name = f'fees.view_{model_name}'
    if model_name == 'group': perm_name = 'auth.view_group'
    
    if not request.user.has_perm(perm_name) and not request.user.is_superuser:
        messages.error(request, f"You don't have permission to view {model_name}s.")
        return redirect('fees:dashboard')
    
    # ISSUE 3 Fix: Handle Bulk Delete
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        # Permission Check: Delete
        del_perm = f'fees.delete_{model_name}'
        if model_name == 'group': del_perm = 'auth.delete_group'
        
        if not request.user.has_perm(del_perm) and not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete these records.")
            return redirect('fees:manage_list', model_name=model_name)

        ids = request.POST.getlist('selected_ids')
        if ids:
            # normalize ids to ints
            try:
                ids_int = [int(i) for i in ids]
            except Exception:
                ids_int = ids

            # If deleting students, prevent deleting ones with related FeeRecord or FeePayment
            if model_name == 'student':
                blocked_ids = set()
                # check fee records
                blocked_ids.update(FeeRecord.objects.filter(student_id__in=ids_int).values_list('student_id', flat=True))
                # check fee payments
                blocked_ids.update(FeePayment.objects.filter(student_id__in=ids_int).values_list('student_id', flat=True))

                deletable = [i for i in ids_int if i not in blocked_ids]

                if deletable:
                    model.objects.filter(pk__in=deletable).delete()
                    messages.success(request, f"Deleted {len(deletable)} {model_name}(s) successfully.")

                if blocked_ids:
                    messages.error(request, f"Cannot delete students with ids: {', '.join(map(str, blocked_ids))}. They have related records.")
            else:
                try:
                    model.objects.filter(pk__in=ids_int).delete()
                    messages.success(request, f"Selected {title} deleted successfully.")
                except Exception:
                    messages.error(request, f"Cannot delete this {model_name}. It may have related records. Please delete related records first.")

        return redirect('fees:manage_list', model_name=model_name)

    objects = model.objects.all()
    
    available_classes = []
    selected_class = None
    
    if model_name == 'student':
        # Get all unique classes, ensure they're integers
        try:
            available_classes = list(Student.objects.values_list('student_class', flat=True).distinct().order_by('student_class'))
            available_classes = [int(c) for c in available_classes if c]  # Convert to int, remove None
        except:
            available_classes = []
        
        # Get selected class from query parameter
        selected_class = request.GET.get('class', '')
        
        # Apply filter if class is selected
        if selected_class:
            try:
                selected_class_int = int(selected_class)
                objects = objects.filter(student_class=selected_class_int)
                # Keep selected_class as int for template comparison
                selected_class = selected_class_int
            except (ValueError, TypeError):
                selected_class = None
        else:
            selected_class = None
    # ISSUE 5 Fix: Readonly for FeeRecord
    readonly = False
    if model_name == 'feerecord':
        readonly = True
    
    # Simple search
    q = request.GET.get('q')
    if q:
        if model_name == 'student':
            objects = objects.filter(name__icontains=q) | objects.filter(roll_no__icontains=q)
        elif model_name == 'customuser':
            objects = objects.filter(username__icontains=q)
            
    return render(request, 'fees/generic_list.html', {
        'objects': objects,
        'fields': fields,
        'title': title,
        'model_name': model_name,
        'readonly': readonly,
        'available_classes': available_classes,
        'selected_class': selected_class,
    })


MODEL_LABELS = {
    'student': 'Student',
    'classfee': 'Class Fee',
    'feepayment': 'Fee Payment',
    'feerecord': 'Fee Record',
    'customuser': 'User',
    'group': 'Group',
}

@login_required
def manage_form(request, model_name, pk=None):
    model_map = {
        'student': (Student, StudentForm),
        'classfee': (ClassFee, ClassFeeForm),
        'feepayment': (FeePayment, FeePaymentForm),
        'feerecord': (FeeRecord, FeeRecordForm),
        'customuser': (CustomUser, CustomUserUpdateForm),
        'group': (Group, GroupForm),
    }
    
    if model_name not in model_map:
        return redirect('fees:dashboard')

    # ADMIN-ONLY Check for Users and Groups
    if model_name in ['customuser', 'group'] and not request.user.is_superuser:
        messages.error(request, "Access Denied: Admin only.")
        return redirect('fees:dashboard')

    # Permission Check: Add/Change
    action = 'change' if pk else 'add'
    perm_name = f'fees.{action}_{model_name}'
    if model_name == 'group': perm_name = f'auth.{action}_group'

    if not request.user.has_perm(perm_name) and not request.user.is_superuser:
        messages.error(request, f"You don't have permission to {action} {model_name}s.")
        return redirect('fees:manage_list', model_name=model_name)
        
    model, form_class = model_map[model_name]
    
    # ISSUE 6 & 7 Fix: Proper form selection
    if model_name == 'customuser' and pk is None:
        form_class = CustomUserCreationForm
    
    instance = get_object_or_404(model, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            label = MODEL_LABELS.get(model_name, model_name.replace('_', ' ').title())
            messages.success(request, f"{label} saved successfully.")
            return redirect('fees:manage_list', model_name=model_name)
    else:
        form = form_class(instance=instance)
        
    return render(request, 'fees/generic_form.html', {
        'my_form': form,
        'title': f"{'Edit' if pk else 'Add'} {MODEL_LABELS.get(model_name, model_name.replace('_', ' ').title())}",
        'model_name': model_name,
    })


@login_required
def monthly_fees(request):
    now = datetime.now()
    y, m = now.year, now.month
    # go back 11 months
    start_date = date(y, m, 1) - timedelta(days=330)
    y, m = start_date.year, start_date.month
    
    months = []
    for _ in range(12):
        label = date(y, m, 1).strftime('%B %Y')
        months.append({'year': y, 'month': m, 'label': label})
        if m == 12: m = 1; y += 1
        else: m += 1

    students = Student.objects.all()
    table = []
    for student in students:
        row = {'student': student, 'amounts': []}
        for mo in months:
            payment_sum = FeePayment.objects.filter(student=student, date__year=mo['year'], date__month=mo['month']).aggregate(total=Sum('amount'))['total']
            if payment_sum:
                row['amounts'].append(float(payment_sum))
            else:
                try:
                    record = FeeRecord.objects.get(student=student, month=mo['label'])
                    if record.status == 'Paid':
                        cf = ClassFee.objects.filter(student_class=student.student_class).first()
                        row['amounts'].append(float(cf.fee_amount if cf else student.total_fees))
                    else: row['amounts'].append(None)
                except FeeRecord.DoesNotExist: row['amounts'].append(None)
        table.append(row)

    current = months[-1]
    students = Student.objects.filter(is_active=True)
    total_expected = sum(float(s.get_total_fee()) for s in students)
    total_collected = float(FeePayment.objects.filter(date__year=current['year'], date__month=current['month']).aggregate(total=Sum('amount'))['total'] or 0)
    total_pending = total_expected - total_collected

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="monthly_summary.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student'] + [m['label'] for m in months])
        for row in table:
            writer.writerow([row['student'].name] + [('' if v is None else f"{v:.2f}") for v in row['amounts']])
        return response

    return render(request, 'fees/monthly_fees.html', {
        'months': months, 'table': table, 'total_expected': total_expected, 'total_collected': total_collected, 'total_pending': total_pending,
    })

@login_required
def set_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        if theme:
            request.user.theme_preference = theme
            request.user.save()
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def students_list(request): return redirect('fees:manage_list', model_name='student')

@login_required
def paid_students_list(request):
    current_month = datetime.now().strftime('%B %Y')
    records = FeeRecord.objects.filter(month=current_month)
    paid_ids = [r.student_id for r in records if r.pending_amount <= 0]
    return render(request, 'fees/generic_list.html', {
        'objects': Student.objects.filter(id__in=paid_ids),
        'title': f'Paid - {current_month}',
        'fields': ['name', 'roll_no', 'student_class'],
        'model_name': 'student',
        'readonly': True
    })

@login_required
def unpaid_students_list(request):
    current_month = datetime.now().strftime('%B %Y')
    records = FeeRecord.objects.filter(month=current_month)
    unpaid_ids = [r.student_id for r in records if r.pending_amount > 0]
    # Also include students without a record for the current month
    all_active_ids = Student.objects.filter(is_active=True).values_list('id', flat=True)
    recorded_ids = records.values_list('student_id', flat=True)
    unrecorded_ids = [i for i in all_active_ids if i not in recorded_ids]
    
    final_ids = list(unpaid_ids) + list(unrecorded_ids)
    
    return render(request, 'fees/generic_list.html', {
        'objects': Student.objects.filter(id__in=final_ids),
        'title': f'Unpaid - {current_month}',
        'fields': ['name', 'roll_no', 'student_class'],
        'model_name': 'student',
        'readonly': True
    })

@login_required
def generate_receipt(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id)
    return HttpResponse(generate_payment_receipt(payment), content_type='application/pdf')

@login_required
def export_fees_excel(request):
    from .utils.reports_excel import export_fees_to_excel
    buffer = export_fees_to_excel(FeeRecord.objects.all())
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="fms_report.xlsx"'
    return response
