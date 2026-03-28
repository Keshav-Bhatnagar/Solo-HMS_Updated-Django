from django import forms
from .models import MessMenu, MessRules, DiscussionMessage, LostItem, FoundItem, ClaimRequest

class MessMenuForm(forms.ModelForm):
    class Meta:
        model = MessMenu
        fields = ['day', 'meal_type', 'menu']
        widgets = {
            'day': forms.Select(choices=[
                ('Monday', 'Monday'),
                ('Tuesday', 'Tuesday'),
                ('Wednesday', 'Wednesday'),
                ('Thursday', 'Thursday'),
                ('Friday', 'Friday'),
                ('Saturday', 'Saturday'),
                ('Sunday', 'Sunday'),
            ]),
            'meal_type': forms.Select(choices=[
                ('Breakfast', 'Breakfast'),
                ('Lunch', 'Lunch'),
                ('Dinner', 'Dinner'),
            ]),
            'menu': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter menu details...', 'class': 'form-control'}),
        }

class MessRulesForm(forms.ModelForm):
    class Meta:
        model = MessRules
        fields = ['rule', 'order']
        widgets = {
            'rule': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter mess rule...', 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }

class DiscussionForm(forms.ModelForm):
    class Meta:
        model = DiscussionMessage
        fields = ['message', 'is_notification']
        widgets = {
            'message': forms.TextInput(attrs={
                'placeholder': 'Type message...',
                'class': 'form-control'
            }),
            'is_notification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not user or not user.is_staff:
            del self.fields['is_notification']

class LostItemForm(forms.ModelForm):
    class Meta:
        model = LostItem
        fields = ['title', 'description', 'category', 'date_lost', 'location', 'contact_info']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Lost Wallet', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the item...', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date_lost': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Library', 'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'placeholder': 'e.g., email@example.com', 'class': 'form-control'}),
        }

class FoundItemForm(forms.ModelForm):
    class Meta:
        model = FoundItem
        fields = ['title', 'description', 'category', 'date_found', 'location', 'contact_info']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Found Keys', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the item...', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date_found': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Cafeteria', 'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'placeholder': 'e.g., email@example.com', 'class': 'form-control'}),
        }

class ClaimRequestForm(forms.ModelForm):
    class Meta:
        model = ClaimRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please provide details to prove this item belongs to you...', 'class': 'form-control'}),
        }