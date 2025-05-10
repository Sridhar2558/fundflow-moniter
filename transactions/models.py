from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('B', 'Bank'),
        ('C', 'Cash'),
        ('D', 'Digital Wallet'),
        ('I', 'Investment'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=20, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('I', 'Income'),
        ('E', 'Expense'),
        ('T', 'Transfer'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For transfers
    to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transfers')
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} on {self.date}"
    
    def save(self, *args, **kwargs):
        # Update account balances when transaction is saved
        super().save(*args, **kwargs)
        self.update_balances()
    
    def update_balances(self):
        if self.transaction_type == 'I':
            self.account.balance += self.amount
            self.account.save()
        elif self.transaction_type == 'E':
            self.account.balance -= self.amount
            self.account.save()
        elif self.transaction_type == 'T' and self.to_account:
            self.account.balance -= self.amount
            self.account.save()
            self.to_account.balance += self.amount
            self.to_account.save()