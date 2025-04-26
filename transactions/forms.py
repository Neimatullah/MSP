from django import forms
from .models import Transaction, Category, Fund, Ledger
from django.contrib.auth.models import User


class AddUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_staff']
        widgets = {
            'password': forms.PasswordInput(),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'category', 'description']  # اضافه کردن description
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان تراکنش را وارد کنید'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مقدار'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات تراکنش (اختیاری)'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']  # اضافه کردن description و is_active
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دسته'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'توضیحات (اختیاری)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name', 'currency', 'description']


class LedgerForm(forms.ModelForm):
    class Meta:
        model = Ledger
        fields = ['transaction_type', 'amount', 'description']
