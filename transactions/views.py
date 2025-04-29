from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Category, Fund, Ledger
from .forms import TransactionForm, FundForm, LedgerForm
import csv
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .forms import AddUserForm
from persiantools.jdatetime import JalaliDateTime


def signup(request):
    return render(request, 'signup.html')


def ledger_view(request, fund_id):
    transactions = Transaction.objects.filter(fund_id=fund_id).order_by('-created_at')
    for transaction in transactions:
        transaction.created_at_jalali = JalaliDateTime(transaction.created_at).strftime('%A، %d %B %Y، %H:%M')

    context = {
        'fund': Fund.objects.get(id=fund_id),
        'transactions': transactions,
    }
    return render(request, 'ledger.html', context)


def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('manage_users')  # هدایت به لیست کاربران
    else:
        form = AddUserForm()
    return render(request, 'add_user.html', {'form': form})


def custom_logout(request):
    logout(request)  # کاربر را از سیستم خارج می‌کند
    return redirect('login')  # هدایت به صفحه لاگین


@user_passes_test(lambda u: u.is_superuser)
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # مسیر قالب لاگین
    redirect_authenticated_user = True  # کاربر لاگین شده را به صفحه دیگر هدایت می‌کند

    def form_valid(self, form):
        # پیام خوشامدگویی پس از ورود موفق
        messages.success(self.request, f"خوش آمدید {self.request.user.username}!")
        return super().form_valid(form)

    def get_success_url(self):
        # مسیر موفقیت پس از ورود
        return self.request.GET.get('next') or '/dashboard/'


@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.delete()
        messages.success(request, f'کاربر {user.email} با موفقیت حذف شد.')
        return redirect('manage_users')
    return render(request, 'delete_user.html', {'user': user})


@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user.email = email
        user.username = email  # جنگو از ایمیل برای username استفاده می‌کند
        if password:
            user.set_password(password)  # رمز عبور را به‌روزرسانی کنید
        user.save()
        messages.success(request, f'اطلاعات کاربر {email} با موفقیت به‌روزرسانی شد.')
        return redirect('manage_users')
    return render(request, 'edit_user.html', {'user': user})


# فقط مدیران مجاز به دسترسی به این ویو هستند
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = User.objects.all()  # دریافت تمامی کاربران
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
            messages.success(request, f'کاربر {email} با موفقیت ایجاد شد.')
        except:
            messages.error(request, 'ایجاد کاربر ناموفق بود. لطفاً دوباره تلاش کنید.')
        return redirect('manage_users')
    return render(request, 'manage_users.html', {'users': users})


@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')


class CustomLoginView(LoginView):
    template_name = 'login.html'  # مسیر قالب صفحه لاگین


class CustomLogoutView(LogoutView):
    next_page = '/login/'  # صفحه‌ای که پس از خروج نمایش داده می‌شود


def detail_ledger(request, transaction_id):
    transaction = get_object_or_404(Ledger, id=transaction_id)  # پیدا کردن تراکنش مرتبط
    context = {'transaction': transaction}  # ارسال داده تراکنش به قالب
    return render(request, 'transactions/detail_ledger.html', context)


def delete_ledger(request, transaction_id):
    transaction = get_object_or_404(Ledger, id=transaction_id)

    if request.method == "POST":
        transaction.delete()
        messages.success(request, f'تراکنش "{transaction.transaction_type}" با موفقیت حذف شد.')
        return redirect('ledger_list', fund_id=transaction.fund.id)  # تغییر مسیر پس از حذف

    # بازگرداندن صفحه تأیید حذف برای درخواست‌های GET
    return render(request, 'transactions/delete_ledger.html', {'transaction': transaction})


def edit_ledger(request, transaction_id):
    transaction = get_object_or_404(Ledger, id=transaction_id)  # پیدا کردن تراکنش
    fund = transaction.fund  # صندوق مرتبط با تراکنش

    if request.method == 'POST':
        form = LedgerForm(request.POST, instance=transaction)  # فرم با داده‌های تراکنش فعلی
        if form.is_valid():
            old_amount = transaction.amount
            old_type = transaction.transaction_type
            transaction = form.save(commit=False)

            # اصلاح موجودی صندوق بر اساس تغییرات
            if old_type == 'RECEIVE':
                fund.balance -= old_amount
            elif old_type == 'PAY':
                fund.balance += old_amount

            if transaction.transaction_type == 'RECEIVE':
                fund.balance += transaction.amount
            elif transaction.transaction_type == 'PAY':
                fund.balance -= transaction.amount

            fund.save()  # ذخیره تغییرات موجودی صندوق
            transaction.save()  # ذخیره تغییرات تراکنش

            # پیام موفقیت پس از ذخیره تغییرات
            messages.success(request, 'تغییرات با موفقیت ذخیره شد.')
            return redirect('ledger_list', fund_id=fund.id)  # بازگشت به لیست تراکنش‌های صندوق
    else:
        form = LedgerForm(instance=transaction)

    return render(request, 'transactions/edit_ledger.html', {'form': form, 'fund': fund})


def add_ledger(request, fund_id):
    fund = get_object_or_404(Fund, id=fund_id)  # پیدا کردن صندوق مرتبط
    if request.method == 'POST':  # اگر داده‌ها ارسال شده باشند
        form = LedgerForm(request.POST)
        if form.is_valid():  # اعتبارسنجی فرم
            transaction = form.save(commit=False)
            transaction.fund = fund  # مرتبط کردن تراکنش با صندوق
            transaction.serial_number = Ledger.objects.filter(fund=fund).count() + 1  # شماره مسلسل خودکار
            transaction.save()

            # به‌روزرسانی موجودی صندوق بر اساس نوع تراکنش
            if transaction.transaction_type == 'RECEIVE':
                fund.balance += transaction.amount
            elif transaction.transaction_type == 'PAY':
                fund.balance -= transaction.amount
            fund.save()

            return redirect('ledger_list', fund_id=fund.id)  # بازگشت به لیست تراکنش‌های صندوق
    else:
        form = LedgerForm()
    return render(request, 'transactions/add_ledger.html', {'form': form, 'fund': fund})


def add_fund(request):
    if request.method == 'POST':  # بررسی اینکه آیا فرم ارسال شده است
        form = FundForm(request.POST)  # دریافت داده‌های ارسال شده
        if form.is_valid():  # بررسی صحت داده‌ها
            form.save()  # ذخیره داده‌های جدید
            return redirect('fund_list')  # بازگشت به لیست صندوق‌ها
    else:
        form = FundForm()  # فرم خالی برای نمایش به کاربر
    return render(request, 'transactions/add_fund.html', {'form': form})


def fund_list(request):
    # محاسبه موجودی بر اساس تراکنش‌ها
    funds = Fund.objects.annotate(
        total_receive=Sum('transactions__amount', filter=Q(transactions__transaction_type='RECEIVE')),
        total_pay=Sum('transactions__amount', filter=Q(transactions__transaction_type='PAY')),
        calculated_balance=(
                Sum('transactions__amount', filter=Q(transactions__transaction_type='RECEIVE')) -
                Sum('transactions__amount', filter=Q(transactions__transaction_type='PAY'))
        )
    )
    context = {'funds': funds}  # ارسال صندوق‌ها و موجودی محاسبه‌شده به قالب
    return render(request, 'transactions/fund_list.html', context)


def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)  # یافتن تراکنش مورد نظر
    if request.method == 'POST':  # تأیید عملیات حذف
        transaction.delete()  # حذف تراکنش
        return redirect('transaction_list')  # بازگشت به لیست تراکنش‌ها
    return render(request, 'transactions/delete.html', {'transaction': transaction})


def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)  # یافتن تراکنش بر اساس کلید اصلی
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()  # ذخیره تغییرات
            return redirect('transaction_list')  # بازگشت به لیست تراکنش‌ها
    else:
        form = TransactionForm(instance=transaction)  # پر کردن فرم با داده‌های قبلی
    return render(request, 'transactions/edit.html', {'form': form, 'transaction': transaction})


def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('transaction_list')  # بازگشت به لیست تراکنش‌ها
    else:
        form = TransactionForm()
    return render(request, 'transactions/add.html', {'form': form})


def dashboard(request):
    # محاسبه درآمد و هزینه‌ها برای دسته‌بندی‌ها
    categories = Category.objects.filter(is_active=True).annotate(
        total_income=Sum('transaction__amount', filter=Q(transaction__transaction_type='INCOME')),
        total_expense=Sum('transaction__amount', filter=Q(transaction__transaction_type='EXPENSE'))
    )

    # محاسبه درآمد و هزینه کلی
    total_income = Transaction.objects.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    # محاسبه درصد پیشرفت درآمد نسبت به هزینه‌ها
    progress_percentage = 0
    if total_expense > 0:
        progress_percentage = round((total_income / total_expense) * 100, 2)  # درصد پیشرفت با دو رقم اعشار

    # دریافت لیست صندوق‌ها و موجودی‌هایشان
    funds = Fund.objects.all()

    # افزودن قابلیت فیلتر تاریخ
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        transactions = Transaction.objects.filter(date__range=[start_date, end_date])
        total_income = transactions.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = transactions.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_income - total_expense
        # محاسبه درصدها
        income_progress = (total_income / (total_income + total_expense)) * 100
        expense_progress = (total_expense / (total_income + total_expense)) * 100
        balance_progress = (balance / total_income) * 100
    # ایجاد کانتکست برای قالب
    context = {
        'categories': categories,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'funds': funds,  # لیست صندوق‌ها
        'progress_percentage': progress_percentage,  # درصد پیشرفت با دو رقم اعشار
        'start_date': start_date,  # تاریخ شروع فیلتر
        'end_date': end_date,  # تاریخ پایان فیلتر
    }
    return render(request, 'transactions/dashboard.html', context)


# گزارش دسته‌بندی‌ها
def category_report(request):
    categories = Category.objects.filter(is_active=True).annotate(
        total_income=Sum('transaction__amount', filter=Q(transaction__transaction_type='INCOME')) or 0,
        total_expense=Sum('transaction__amount', filter=Q(transaction__transaction_type='EXPENSE')) or 0
    )
    total_income = sum(cat.total_income or 0 for cat in categories)
    total_expense = sum(cat.total_expense or 0 for cat in categories)
    balance = total_income - total_expense

    context = {
        'categories': categories,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
    }
    return render(request, 'transactions/category_report.html', context)


# لیست تراکنش‌ها
def transaction_list(request):
    transactions = Transaction.objects.all().order_by('-created_at')

    # فیلتر براساس تاریخ و دسته‌بندی
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_id = request.GET.get('category_id')

    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    total_income = transactions.filter(transaction_type='RECEIVE').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(transaction_type='PAY').aggregate(Sum('amount'))['amount__sum'] or 0
    total_balance = total_income - total_expense

    context = {
        'transactions': transactions,
        'total_receive': total_income,
        'total_pay': total_expense,
        'balance': total_balance,
        'start_date': start_date,
        'end_date': end_date,
        'category_id': category_id,
    }
    return render(request, 'transactions/list.html', context)


# لیست تراکنش‌های صندوق
def ledger_list(request, fund_id):
    fund = get_object_or_404(Fund, id=fund_id)
    transactions = fund.transactions.filter(is_archived=False).order_by('created_at')  # ترتیب صعودی

    # دریافت پارامترهای جستجو و فیلتر
    search_query = request.GET.get('search_query', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # فیلتر جستجو
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) |
            Q(transaction_type__icontains=search_query)
        )
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)

    # محاسبه بیلانس برای هر تراکنش
    balance = 0
    for transaction in transactions:
        if transaction.transaction_type == 'RECEIVE':
            balance += transaction.amount
        elif transaction.transaction_type == 'PAY':
            balance -= transaction.amount
        transaction.balance = balance  # مقدار بیلانس به تراکنش اضافه می‌شود

    # مجموع دریافت‌ها و پرداخت‌ها
    total_receive = transactions.filter(transaction_type='RECEIVE').aggregate(Sum('amount'))['amount__sum'] or 0
    total_pay = transactions.filter(transaction_type='PAY').aggregate(Sum('amount'))['amount__sum'] or 0
    fund.balance = total_receive - total_pay  # محاسبه موجودی کل

    context = {
        'fund': fund,
        'transactions': transactions,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'total_receive': total_receive,
        'total_pay': total_pay,
    }
    return render(request, 'transactions/ledger_list.html', context)


# صادرات CSV تراکنش‌ها
def export_ledger_csv(request, fund_id):
    fund = get_object_or_404(Fund, id=fund_id)
    transactions = fund.transactions.filter(is_archived=False)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{fund.name}_ledger.csv"'

    writer = csv.writer(response)
    writer.writerow(['شماره مسلسل', 'نوع تراکنش', 'مقدار', 'توضیحات', 'تاریخ'])

    for transaction in transactions:
        writer.writerow([
            transaction.serial_number,
            transaction.transaction_type,
            transaction.amount,
            transaction.short_description(),
            transaction.created_at,
        ])

    return response


# آرشیو تراکنش
def archive_ledger(request, transaction_id):
    transaction = get_object_or_404(Ledger, id=transaction_id)
    transaction.archive()
    return redirect('ledger_list', fund_id=transaction.fund.id)
