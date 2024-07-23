from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from django.core.exceptions import ValidationError

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
    
# ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'avatar']

    def clean_avatar(self):
        image = self.cleaned_data.get('avatar')
        if image:
            # if image.content_type not in ALLOWED_IMAGE_TYPES:
            #     print('형식!')
            #     raise ValidationError('허용되지 않는 이미지 형식입니다. JPEG 또는 PNG 파일만 업로드할 수 있습니다.')
            if image.size > 5 * 1024 * 1024:  # 5MB로 파일 크기 제한
                print('용량!')
                raise ValidationError('이미지 파일의 크기는 5MB를 초과할 수 없습니다.')
        return image