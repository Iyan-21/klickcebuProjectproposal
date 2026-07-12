from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control-kc'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control-kc'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control-kc'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control-kc'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control-kc'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control-kc'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'contact_number', 'facebook_url', 'address', 'valid_id']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control-kc'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control-kc'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control-kc', 'placeholder': '09XX-XXX-XXXX'}),
            'facebook_url': forms.TextInput(attrs={'class': 'form-control-kc', 'placeholder': 'facebook.com/yourprofile'}),
            'address': forms.TextInput(attrs={'class': 'form-control-kc', 'placeholder': 'Pickup/delivery address'}),
        }