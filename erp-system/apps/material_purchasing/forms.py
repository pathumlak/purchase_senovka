from django import forms
from .models import MaterialPurchase

_text = 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400'
_sel  = 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition bg-white'
_ta   = 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400 resize-none'


class MaterialPurchaseForm(forms.ModelForm):
    class Meta:
        model = MaterialPurchase
        fields = [
            'supplier_name', 'invoice_number', 'received_date',
            'material_name', 'quantity', 'unit_type', 'unit_price',
            'scale_weight', 'weight_verified', 'notes',
        ]
        widgets = {
            'supplier_name': forms.TextInput(attrs={
                'class': _text, 'placeholder': 'Supplier name',
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': _text, 'placeholder': 'Invoice / bill number',
            }),
            'received_date': forms.DateInput(attrs={
                'class': _text, 'type': 'date',
            }),
            'material_name': forms.TextInput(attrs={
                'class': _text, 'placeholder': 'Material name',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': _text, 'placeholder': '0.000', 'step': '0.001', 'min': '0.001',
                'id': 'id_quantity',
            }),
            'unit_type': forms.Select(attrs={'class': _sel, 'id': 'id_unit_type'}),
            'unit_price': forms.NumberInput(attrs={
                'class': _text, 'placeholder': '0.00', 'step': '0.01', 'min': '0',
                'id': 'id_unit_price',
            }),
            'scale_weight': forms.NumberInput(attrs={
                'class': _text, 'placeholder': '0.000 (optional)', 'step': '0.001', 'min': '0',
                'id': 'id_scale_weight',
            }),
            'weight_verified': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500',
                'id': 'id_weight_verified',
            }),
            'notes': forms.Textarea(attrs={
                'class': _ta, 'rows': 3, 'placeholder': 'Additional notes (optional)',
            }),
        }
        labels = {
            'scale_weight': 'Scale Weight (Actual)',
            'weight_verified': 'Mark as weight-verified',
        }
