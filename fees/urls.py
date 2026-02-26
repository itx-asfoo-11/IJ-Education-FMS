from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('set-theme/', views.set_theme, name='set_theme'),
    
    # Generic Management
    path('manage/<str:model_name>/', views.manage_list, name='manage_list'),
    path('manage/<str:model_name>/add/', views.manage_form, name='manage_form'),
    path('manage/<str:model_name>/edit/<int:pk>/', views.manage_form, name='manage_form_pk'),

    path('students/', views.students_list, name='students_list'),
    path('students/paid/', views.paid_students_list, name='paid_students_list'),
    path('students/unpaid/', views.unpaid_students_list, name='unpaid_students_list'),
    path('monthly-fees/', views.monthly_fees, name='monthly_fees'),
    path('receipt/<int:payment_id>/', views.generate_receipt, name='generate_receipt'),
    path('export/fees/', views.export_fees_excel, name='export_fees_excel'),
]
