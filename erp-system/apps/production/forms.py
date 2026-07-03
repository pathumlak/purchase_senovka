from django import forms
from .models import ProductCategory, Product, DailyRunningMachine, Machine, DailyWorkAssignment, Employee, ProductionItem, ShiftTemplate, TargetLog


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Category Description'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'qty', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': 'Product name',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition bg-white',
            }),
            'size': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': 'e.g. 1 inch, 500ml, Large',
            }),
            'qty': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400 resize-none',
                'placeholder': 'Product description...',
                'rows': 3,
            }),
        }


_INPUT = 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400'


class DailyRunningMachineForm(forms.ModelForm):
    class Meta:
        model = DailyRunningMachine
        fields = [
            'production_date', 'machine_name', 'machine_not_working',
            'item', 'machine_operator', 'notes',
        ]
        widgets = {
            'production_date': forms.DateInput(attrs={
                'class': _INPUT,
                'type': 'date',
            }),
            'machine_name': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Machine name',
            }),
            'machine_not_working': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'item': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition bg-white',
            }),
            'machine_operator': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Operator name',
            }),
            'notes': forms.Textarea(attrs={
                'class': f'{_INPUT} resize-none',
                'placeholder': 'Optional notes',
                'rows': 2,
            }),
        }

    def clean(self):
        cleaned = super().clean()
        not_working = cleaned.get('machine_not_working', False)
        if not not_working:
            if not cleaned.get('item'):
                self.add_error('item', 'Item is required when the machine is working.')
            if not cleaned.get('machine_operator', '').strip():
                self.add_error('machine_operator', 'Operator is required when the machine is working.')
        return cleaned


class DailyWorkAssignmentForm(forms.ModelForm):
    class Meta:
        model = DailyWorkAssignment
        fields = ['production_date', 'crusher_operator', 'material_mixer', 'extra_work_employee']
        widgets = {
            'production_date': forms.DateInput(attrs={
                'class': _INPUT,
                'type': 'date',
            }),
            'crusher_operator': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Employee name',
            }),
            'material_mixer': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Employee name',
            }),
            'extra_work_employee': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Employee name',
            }),
        }


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400',
                'placeholder': 'Machine name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400 resize-none',
                'placeholder': 'Optional description',
                'rows': 2,
            }),
        }


_I = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition placeholder-gray-400'
_S = f'{_I} bg-white'


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': _I, 'placeholder': 'Employee name'}),
        }


class ProductionItemForm(forms.ModelForm):
    class Meta:
        model = ProductionItem
        fields = ['name', 'hourly_qty', 'description', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': _I, 'placeholder': 'Item name'}),
            'hourly_qty': forms.NumberInput(attrs={'class': _I, 'placeholder': '160', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': f'{_I} resize-none', 'rows': 2, 'placeholder': 'Optional notes'}),
        }


class ShiftTemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplate
        fields = ['name', 'start_time', 'end_time', 'crosses_midnight']
        widgets = {
            'name': forms.TextInput(attrs={'class': _I, 'placeholder': 'e.g. 8am – 5pm'}),
            'start_time': forms.TimeInput(attrs={'class': _I, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': _I, 'type': 'time'}),
        }


class TargetLogForm(forms.ModelForm):
    class Meta:
        model = TargetLog
        fields = [
            'date', 'employee', 'machine_name', 'item', 'shift_template',
            'cavity', 'cycle_time_seconds', 'target_qty', 'actual_qty',
            'downtime_minutes', 'downtime_reason', 'point', 'remarks',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': _I, 'type': 'date'}),
            'employee': forms.Select(attrs={'class': _S}),
            'machine_name': forms.TextInput(attrs={'class': _I, 'placeholder': 'Machine / mould name'}),
            'item': forms.Select(attrs={'class': _S}),
            'shift_template': forms.Select(attrs={'class': _S}),
            'cavity': forms.NumberInput(attrs={'class': _I, 'min': '1', 'value': '1'}),
            'cycle_time_seconds': forms.NumberInput(attrs={'class': _I, 'min': '1', 'placeholder': 'Optional'}),
            'target_qty': forms.NumberInput(attrs={'class': _I, 'min': '0'}),
            'actual_qty': forms.NumberInput(attrs={'class': _I, 'min': '0'}),
            'downtime_minutes': forms.NumberInput(attrs={'class': _I, 'min': '0', 'step': '0.01', 'value': '0'}),
            'downtime_reason': forms.TextInput(attrs={'class': _I, 'placeholder': 'Reason (if any)'}),
            'point': forms.Select(attrs={'class': _S}),
            'remarks': forms.TextInput(attrs={'class': _I, 'placeholder': 'Optional remarks'}),
        }