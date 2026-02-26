from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime
import bcrypt


SECURITY_QUESTIONS = [
    ('mother_name', "What is your mother's name?"),
    ('favorite_color', 'What is your favorite color?'),
    ('pet_name', "What is your pet's name?"),
    ('birth_city', 'What city were you born in?'),
    ('favorite_food', 'What is your favorite food?'),
]


THEME_CHOICES = [
    ('midnight-blue', 'Midnight Blue'),
    ('clean-light', 'Clean Light'),
    ('royal-purple', 'Royal Purple'),
    ('rose-gold', 'Rose Gold'),
    ('sunset-orange', 'Sunset Orange'),
    ('ocean-blue', 'Ocean Blue'),
    ('forest-green', 'Forest Green'),
    ('crimson-red', 'Crimson Red'),
    ('gold-standard', 'Gold Standard'),
    ('chocolate-brown', 'Chocolate Brown'),
]


class CustomUser(AbstractUser):
    security_question = models.CharField(max_length=64, choices=SECURITY_QUESTIONS, blank=True, null=True)
    security_answer = models.CharField(max_length=128, blank=True, null=True)
    theme_preference = models.CharField(max_length=32, choices=THEME_CHOICES, default='midnight-blue')

    def set_security_answer(self, raw_answer: str):
        if not raw_answer:
            self.security_answer = None
            return
        # Ensure answer is treated as string & lowercased for better UX (optional but common)
        raw_answer = str(raw_answer).strip().lower()
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(raw_answer.encode('utf-8'), salt)
        self.security_answer = hashed.decode('utf-8')

    def check_security_answer(self, raw_answer: str) -> bool:
        if not self.security_answer or not raw_answer:
            return False
        
        raw_answer = str(raw_answer).strip().lower()
        
        # Check if it looks like a bcrypt hash (starts with $2b$)
        if self.security_answer.startswith('$2b$'):
            try:
                return bcrypt.checkpw(raw_answer.encode('utf-8'), self.security_answer.encode('utf-8'))
            except Exception:
                return False
        
        # Fallback for plain text (migration will handle most cases, but safety first)
        return self.security_answer == raw_answer


class Student(models.Model):
    name = models.CharField(max_length=255)
    roll_no = models.IntegerField(unique=True)
    student_class = models.CharField(max_length=64)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    manual_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.roll_no})"

    def get_total_fee(self):
        """Return manual_fee if set, else the class fee amount or the student's total_fees."""
        if self.manual_fee is not None:
            return float(self.manual_fee)
        try:
            cf = ClassFee.objects.get(student_class=self.student_class)
            return float(cf.fee_amount)
        except ClassFee.DoesNotExist:
            return float(self.total_fees)


class ClassFee(models.Model):
    student_class = models.CharField(max_length=64, unique=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.student_class}: {self.fee_amount}"


class FeeRecord(models.Model):
    STATUS_CHOICES = [('Paid', 'Paid'), ('Unpaid', 'Unpaid')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.CharField(max_length=32)
    due_date = models.DateField()
    submission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Unpaid')

    class Meta:
        unique_together = ('student', 'month')

    @property
    def paid_amount(self):
        try:
            from .models import FeePayment
            md = datetime.strptime(self.month, "%B %Y")
            # Sum all payments for this student in this specific month/year
            return float(FeePayment.objects.filter(
                student=self.student, 
                date__year=md.year, 
                date__month=md.month
            ).aggregate(total=Sum('amount'))['total'] or 0)
        except Exception as e:
            return 0.0

    @property
    def pending_amount(self):
        return max(0.0, float(self.student.get_total_fee()) - self.paid_amount)

    def __str__(self):
        return f"{self.student} - {self.month} - {self.status}"


class FeePayment(models.Model):
    PAYMENT_CHOICES = [('Cash', 'Cash'), ('Online', 'Online')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student} - {self.amount} on {self.date}"

class GlobalSettings(models.Model):
    late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    school_name = models.CharField(max_length=255, default="FMS PRO Academy")
    school_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Global Settings"

    class Meta:
        verbose_name_plural = "Global Settings"
