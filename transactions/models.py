from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)  # توضیحات دسته‌بندی
    is_active = models.BooleanField(default=True)  # وضعیت فعال/غیرفعال
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # دسته اصلی (برای زیرمجموعه)

    def __str__(self):
        return self.name

    def has_children(self):
        return Category.objects.filter(parent=self).exists()

    def total_transactions_by_type(self, transaction_type):
        return self.transaction_set.filter(transaction_type=transaction_type).aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # تاریخ ویرایش
    description = models.TextField(blank=True, null=True)  # توضیحات تراکنش
    invoice_number = models.CharField(max_length=50, blank=True, null=True)  # شماره فاکتور

    def __str__(self):
        return f"{self.title} - {self.transaction_type} - {self.formatted_amount()}"

    def formatted_amount(self):
        return f"{self.amount:,.2f}"  # فرمت نمایش اعداد

    def get_category_name(self):
        return self.category.name if self.category else "بدون دسته‌بندی"


class Fund(models.Model):
    CURRENCY_CHOICES = [
        ('AFN', 'افغانی'),
        ('USD', 'دالر'),
        ('EUR', 'یورو'),
        ('GBP', 'پوند'),
    ]

    name = models.CharField(max_length=100, unique=True)  # نام صندوق
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)  # ارز صندوق
    description = models.TextField(blank=True, null=True)  # توضیحات صندوق
    created_at = models.DateTimeField(auto_now_add=True)  # تاریخ ایجاد صندوق
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # موجودی صندوق

    def __str__(self):
        return f"{self.name} - {self.currency}"

    def total_received(self):
        return self.transactions.filter(transaction_type='RECEIVE').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def total_paid(self):
        return self.transactions.filter(transaction_type='PAY').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def update_balance(self):
        self.balance = self.total_received() - self.total_paid()
        self.save()


class Ledger(models.Model):
    TRANSACTION_TYPES = [
        ('RECEIVE', 'دریافت'),
        ('PAY', 'پرداخت'),
    ]

    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='transactions')  # صندوق مرتبط
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)  # نوع تراکنش
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # مقدار تراکنش
    description = models.TextField(blank=True, null=True)  # توضیحات تراکنش
    serial_number = models.PositiveIntegerField(editable=False)  # شماره مسلسل اختصاصی هر صندوق
    created_at = models.DateTimeField(auto_now_add=True)  # تاریخ ایجاد تراکنش
    is_archived = models.BooleanField(default=False)  # وضعیت آرشیو تراکنش

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.fund.name}"

    def save(self, *args, **kwargs):
        """
        تولید شماره مسلسل به صورت اختصاصی برای هر صندوق.
        """
        if not self.serial_number:
            last_transaction = Ledger.objects.filter(fund=self.fund).order_by('-serial_number').first()
            self.serial_number = last_transaction.serial_number + 1 if last_transaction else 1
        super(Ledger, self).save(*args, **kwargs)

    def archive(self):
        """
        تغییر وضعیت تراکنش به آرشیوشده.
        """
        self.is_archived = True
        self.save()

    def short_description(self):
        """
        خلاصه توضیحات تراکنش.
        """
        return self.description[:50] + '...' if self.description and len(self.description) > 50 else self.description
