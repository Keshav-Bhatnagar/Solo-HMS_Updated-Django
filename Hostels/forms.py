from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, FeePayment, ComplaintMaintenance, Feedback

# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, StudentProfile
import re

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'your.email@example.com'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))

    def clean_username(self):
        email = self.cleaned_data.get('username')
        if not CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is not registered.")
        return email

class SignupForm(UserCreationForm):
    contact_number = forms.CharField(max_length=15, required=True)
    terms = forms.BooleanField(required=True, error_messages={'required': 'You must agree to the terms and conditions.'})

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'contact_number', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if not re.match(r'^\+?1?\d{9,15}$', contact_number):
            raise ValidationError("Enter a valid phone number (e.g., +1234567890).")
        return contact_number

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number')
        if roll_number and CustomUser.objects.filter(roll_number=roll_number).exists():
            raise ValidationError("This roll number is already in use.")
        return roll_number

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        if password1 and len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password2
    
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['contact_number', 'profile_picture', 'bio']

class UserAdminEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'is_active', 'is_staff')
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'roll_number': forms.TextInput(attrs={'placeholder': 'Roll Number'}),
        }
        
        
class CardPaymentForm(forms.Form):
    card_number = forms.CharField(label='Card Number', max_length=19)
    expiry_date = forms.CharField(label='Expiry Date (MM/YY)', max_length=5)
    cvc = forms.CharField(label='CVC', max_length=3)
    
    
class PaymentForm(forms.ModelForm):
    card_number = forms.CharField(label='Card Number', max_length=19, required=True)
    expiry_date = forms.CharField(label='Expiry (MM/YY)', max_length=5, required=True)
    cvc = forms.CharField(label='CVC', max_length=3, required=True)

    class Meta:
        model = FeePayment
        fields = ['amount', 'receipt']
        widgets = {
            'amount': forms.NumberInput(attrs={'readonly': 'readonly'})
        }
        

class ComplaintMaintenanceForm(forms.ModelForm):
    class Meta:
        model = ComplaintMaintenance
        fields = ['request_type', 'room_number', 'category', 'details']

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    ENVIRONMENT_RATINGS = [
        ('poor', 'Poor'),
        ('average', 'Average'),
        ('good', 'Good'),
    ]
    environment_rating = forms.ChoiceField(choices=ENVIRONMENT_RATINGS)
    service_rating = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 6)])

    class Meta:
        model = Feedback
        fields = ['hostel', 'environment_rating', 'service_rating', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
        

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class StaffSignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Automatically set as staff
        if commit:
            user.save()
        return user
    
from django import forms
from app2.models import Form

class EventForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['name', 'date', 'time', 'venue', 'organizer' ,'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
        
        
from django import forms
from .models import RoomChangeRequest, Room


class RoomChangeRequestForm(forms.ModelForm):
    class Meta:
        model = RoomChangeRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please provide the reason for requesting a room change',
                'class': 'form-control'
            }),
        }
