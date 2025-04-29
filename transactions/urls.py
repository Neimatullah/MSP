from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from .views import manage_users, edit_user, delete_user, custom_logout

urlpatterns = [
    # صفحه لاگین (اولین صفحه)
    path('', LoginView.as_view(template_name='registration/login.html'), name='login'),

    # داشبورد
    path('dashboard/', views.dashboard, name='dashboard'),

    # تراکنش‌ها
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('transactions/report/', views.category_report, name='category_report'),

    # صندوق‌ها
    path('funds/', views.fund_list, name='fund_list'),
    path('funds/add/', views.add_fund, name='add_fund'),
    path('funds/<int:fund_id>/ledger/', views.ledger_list, name='ledger_list'),
    path('funds/<int:fund_id>/add_ledger/', views.add_ledger, name='add_ledger'),
    path('funds/<int:transaction_id>/edit_ledger/', views.edit_ledger, name='edit_ledger'),
    path('funds/<int:transaction_id>/delete_ledger/', views.delete_ledger, name='delete_ledger'),
    path('funds/<int:transaction_id>/archive_ledger/', views.archive_ledger, name='archive_ledger'),
    path('funds/<int:transaction_id>/detail/', views.detail_ledger, name='detail_ledger'),
    path('funds/<int:fund_id>/export_csv/', views.export_ledger_csv, name='export_ledger_csv'),

    # مدیریت کاربران
    path('manage_users/', manage_users, name='manage_users'),
    path('edit_user/<int:user_id>/', edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', delete_user, name='delete_user'),

    # خروج
    path('logout/', custom_logout, name='logout'),

    path('signup/', views.signup, name='signup'),
    # مسیرهای دیگر...
]
