from django import forms
from .models import Customer, CustomerProductPrice


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'address', 'balance']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': 'Customer name',
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400 resize-none',
                'placeholder': 'Customer address...',
                'rows': 3,
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': '0.00',
                'step': '0.01',
            }),
        }


class CustomerProductPriceForm(forms.ModelForm):
    class Meta:
        model = CustomerProductPrice
        fields = ['customer', 'product', 'unit_price']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition bg-white',
            }),
            'product': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition bg-white',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': '0.00',
                'step': '0.01',
            }),
        }
