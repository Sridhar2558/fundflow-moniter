from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Account, Transaction, Category
from .forms import AccountForm, TransactionForm, CategoryForm
from django.db.models import Q, Sum
@login_required
def dashboard(request):
    accounts = Account.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-date', '-created_at')[:5]  # Only last 5
    
    # Calculate summary statistics
    total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
    income = Transaction.objects.filter(
        user=request.user, 
        transaction_type='I',
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    expenses = Transaction.objects.filter(
        user=request.user, 
        transaction_type='E',
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'accounts': accounts,
        'transactions': transactions,  # Now only 5
        'total_balance': total_balance,
        'income': income,
        'expenses': expenses,
    }
    return render(request, 'transactions/dashboard.html', context)

@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'transactions/account_list.html', {'accounts': accounts})

@login_required
def account_detail(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    transactions = account.transactions.all().order_by('-date')
    return render(request, 'transactions/account_detail.html', {
        'account': account,
        'transactions': transactions
    })

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user)
    return render(request, 'transactions/transaction_form.html', {'form': form})

from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Transaction, Category, Account
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, Category, Account
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, Category, Account
@login_required
def cash_flow_report(request):
    # Get monthly data for the user's transactions
    months = Transaction.objects.filter(user=request.user).dates('date', 'month')
    
    # Prepare the report data
    report_data = []
    category_insights = []
    account_insights = []

    for month in months:
        income = Transaction.objects.filter(
            user=request.user,
            transaction_type='I',
            date__year=month.year,
            date__month=month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Transaction.objects.filter(
            user=request.user,
            transaction_type='E',
            date__year=month.year,
            date__month=month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        report_data.append({
            'month': month,
            'income': income,
            'expenses': expenses,
            'net': income - expenses
        })
    
    # Get data from the last 6 months
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Category Insights
    categories = Category.objects.filter(user=request.user)
    category_expense_totals = []
    
    for category in categories:
        cat_expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='E',
            category=category,
            date__gte=six_months_ago
        ).aggregate(total=Sum('amount'))['total'] or 0

        if cat_expense > 0:
            category_expense_totals.append({
                'name': category.name,
                'amount': cat_expense
            })

    total_category_expenses = sum(c['amount'] for c in category_expense_totals) or 1

    for c in category_expense_totals:
        c['percentage'] = (c['amount'] / total_category_expenses) * 100
        category_insights.append(c)

    category_insights = sorted(category_insights, key=lambda x: x['amount'], reverse=True)

    # Account Insights
    accounts = Account.objects.filter(user=request.user)
    for account in accounts:
        balance_change = Transaction.objects.filter(
            user=request.user,
            account=account,
            date__gte=six_months_ago
        ).aggregate(
            income=Sum('amount', filter=Q(transaction_type='I')),
            expenses=Sum('amount', filter=Q(transaction_type='E'))
        )
        net_change = (balance_change['income'] or 0) - (balance_change['expenses'] or 0)
        account_insights.append({
            'name': account.name,
            'net_change': net_change,
            'current_balance': account.balance
        })

    # Get top 2 performing accounts (highest net change)
    top_performing_accounts = sorted(
        [acc for acc in account_insights if acc['net_change'] > 0],
        key=lambda x: x['net_change'],
        reverse=True
    )[:2]

    # Get top 2 income accounts
    top_income_accounts = Account.objects.filter(
        user=request.user,
        transactions__transaction_type='I',
        transactions__date__gte=six_months_ago
    ).annotate(
        income=Sum('transactions__amount')
    ).filter(income__gt=0).order_by('-income')[:2]

    # Get top 2 expense accounts
    top_expense_accounts = Account.objects.filter(
        user=request.user,
        transactions__transaction_type='E',
        transactions__date__gte=six_months_ago
    ).annotate(
        expenses=Sum('transactions__amount')
    ).filter(expenses__gt=0).order_by('-expenses')[:2]

    # Prepare data for charts
    months_formatted = [data['month'].strftime("%b %Y") for data in report_data[-12:]]
    income_data = [float(data['income']) for data in report_data[-12:]]
    expenses_data = [float(data['expenses']) for data in report_data[-12:]]
    net_data = [float(data['net']) for data in report_data[-12:]]

    category_names = [c['name'] for c in category_insights[:5]]
    category_amounts = [float(c['amount']) for c in category_insights[:5]]

    # Fixed average monthly net calculation
    valid_months = [m for m in report_data[-12:] if m['income'] != 0 or m['expenses'] != 0]
    average_monthly_net = sum(m['net'] for m in valid_months) / len(valid_months) if valid_months else 0

    # Prepare context data
    context = {
        'report_data': report_data[-12:],
        'category_insights': category_insights[:5],
        'account_insights': account_insights,
        'top_performing_accounts': top_performing_accounts,
        'top_income_accounts': top_income_accounts,
        'top_expense_accounts': top_expense_accounts,
        'total_balance': float(sum(acc['current_balance'] for acc in account_insights)),
        'average_monthly_net': float(average_monthly_net),
        'months_formatted': months_formatted,
        'income_data': income_data,
        'expenses_data': expenses_data,
        'net_data': net_data,
        'category_names': category_names,
        'category_amounts': category_amounts,
    }

    return render(request, 'transactions/cash_flow_report.html', context)

# transactions/views.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def add_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'transactions/account_form.html', {'form': form})

@login_required
def edit_account(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('account_detail', pk=account.id)
    else:
        form = AccountForm(instance=account)
    return render(request, 'transactions/account_form.html', {'form': form})