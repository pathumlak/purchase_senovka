from django import forms

from .models import CashSale


class CashSaleForm(forms.ModelForm):
    class Meta:
        model = CashSale
        fields = [
            'date',
            'reference_number',
            'sale_type',
            'amount',
            'purpose',
            'notes',
            'bill_image',
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300',
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300',
                'placeholder': 'e.g. INV-0042',
            }),
            'sale_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-300',
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300',
                'placeholder': '0.00',
            }),
            'purpose': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300',
                'placeholder': 'e.g. Grocery supplies, Utility bill…',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300 resize-none',
                'placeholder': 'Any extra details…',
            }),
            'bill_image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer',
                'accept': 'image/*',
            }),
        }