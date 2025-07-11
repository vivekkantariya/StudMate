from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from .models import Content
from django.core.exceptions import ValidationError

class CustomUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Start typing your name. It will automatically begin with "@". Only lowercase letters, digits, and underscores (_) are allowed.'
        self.fields['password1'].help_text = 'At least 8 characters.'
        self.fields['password2'].help_text = 'Repeat the same password.'

    def clean_username(self):
        raw = self.cleaned_data.get('username', '')
        if not raw.startswith('@'):
            raw = '@' + raw

        core_username = raw[1:]
        
        if len(core_username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

        if not re.fullmatch(r'[a-z0-9_]+', core_username):
            raise ValidationError(
                "Username can only contain lowercase letters, numbers, and underscores. No spaces or special characters allowed."
            )

        # Check uniqueness manually
        if User.objects.filter(username=raw).exists():
            raise ValidationError("This username is already taken.")
        
        return raw

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['name', 'desc', 'content_type', 'tags', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. physics, formulas, semester2'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file type
            if not file.name.endswith(('.pdf', '.docx', '.zip')):
                raise forms.ValidationError("Only .pdf, .docx, or .zip files are allowed.")
            
            # Check file size 
            if file.size > 10 * 1024 * 1024:  #mb
                raise forms.ValidationError("File size should not exceed 5MB.")
        return file

    def clean_tags(self):
        tags_str = self.cleaned_data['tags']
        tag_set = set(tag.strip().lower() for tag in tags_str.split(',') if tag.strip())
        if not (3 <= len(tag_set) <= 5):
            raise forms.ValidationError("Please enter between 3 to 5 unique tags.")
        return ', '.join(tag_set)

