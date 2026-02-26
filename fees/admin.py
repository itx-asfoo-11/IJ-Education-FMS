from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Student, ClassFee, FeeRecord, FeePayment


from django.urls import reverse
from django.utils.html import format_html


admin.site.site_header = "FMS Administration"
admin.site.index_title = "Dashboard"

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Security', {'fields': ('security_question', 'security_answer')}),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'student_class', 'manual_fee', 'display_total_fee')
    search_fields = ('name', 'roll_no', 'student_class')

    def display_total_fee(self, obj):
        try:
            return obj.get_total_fee()
        except Exception:
            return obj.total_fees
    display_total_fee.short_description = 'Effective Fee'

@admin.register(ClassFee)
class ClassFeeAdmin(admin.ModelAdmin):
    list_display = ('student_class', 'fee_amount')

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'status', 'due_date', 'submission_date')
    list_filter = ('status', 'month')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_mode', 'date')
    list_filter = ('payment_mode',)

    def changelist_view(self, request, extra_context=None):
        # This is just to ensure it works, but for index page we need something else
        return super().changelist_view(request, extra_context=extra_context)

# Override admin site index to include stats
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum

original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}
    
    current_month = timezone.now().strftime('%B %Y')
    
    extra_context['total_students'] = Student.objects.count()
    extra_context['collected'] = FeePayment.objects.filter(
        date__month=timezone.now().month, 
        date__year=timezone.now().year
    ).aggregate(total=Sum('amount'))['total'] or 0
    extra_context['pending'] = FeeRecord.objects.filter(
        month=current_month, 
        status='Unpaid'
    ).count()
    
    return original_index(request, extra_context)

admin.site.index = custom_admin_index
