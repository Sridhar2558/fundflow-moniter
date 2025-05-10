from django import forms
from .models import Account, Transaction, Category

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'balance', 'currency']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']

from django import forms
from .models import Transaction
from django.forms.widgets import DateInput

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'amount', 'transaction_type', 'category', 'description', 'date', 'to_account']
        widgets = {
            'date': DateInput(attrs={'type': 'date', 'class': 'form-control datepicker'}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(user=user)
        self.fields['to_account'].queryset = Account.objects.filter(user=user)
        self.fields['category'].queryset = Category.objects.filter(user=user)