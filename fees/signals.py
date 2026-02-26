from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Student, FeePayment, FeeRecord
from datetime import datetime

@receiver(post_save, sender=Student)
def create_initial_fee_record(sender, instance, created, **kwargs):
    if created:
        month_str = datetime.now().strftime("%B %Y")
        due_date = datetime.now().replace(day=10).date()
        FeeRecord.objects.get_or_create(
            student=instance,
            month=month_str,
            defaults={'due_date': due_date, 'status': 'Unpaid'}
        )

@receiver([post_save, post_delete], sender=FeePayment)
def sync_fee_record_status(sender, instance, **kwargs):
    month_str = instance.date.strftime("%B %Y")
    record, created = FeeRecord.objects.get_or_create(
        student=instance.student,
        month=month_str,
        defaults={'due_date': instance.date.replace(day=10), 'status': 'Unpaid'}
    )
    
    # record.pending_amount is a dynamic property that uses the current DB state
    if record.pending_amount <= 0:
        record.status = 'Paid'
        record.submission_date = instance.date
    else:
        record.status = 'Unpaid'
        record.submission_date = None
    record.save()
