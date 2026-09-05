from django import forms
from .models import QuoteRequest

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['product', 'quantity', 'design_file', 'customer_notes']
        widgets = {
            'customer_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Please use matte finish...'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
        }