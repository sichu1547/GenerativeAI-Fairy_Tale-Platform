from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='이메일 주소')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user    

class PasswordResetForm(forms.Form):
    username = forms.CharField(max_length=150, label="사용자 이름")
    email = forms.EmailField(label="이메일 주소")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")
        if not User.objects.filter(username=username, email=email).exists():
            raise forms.ValidationError("사용자 이름 또는 이메일이 잘못되었습니다.")
        return cleaned_data
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'avatar']