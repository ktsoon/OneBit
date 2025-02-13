from django import forms
from .models import *

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class LoginForm(forms.Form):
    """ Авторизация """

    username = forms.CharField(max_length=65)
    password = forms.CharField(max_length=65, widget=forms.PasswordInput)
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""
        self.fields['username'].label = "Логин"
        self.fields['password'].label = "Пароль"

class RegisterForm(UserCreationForm):
    """ Регистрация """

    class Meta:
        model=User
        fields = ['username','email','password1','password2']
        widgets = {
            'email': forms.fields.TextInput(attrs={
                'placeholder': '',
                'label': 'Адрес электронной почты',
                'required': True
                }),
            }
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = "Логин"
        self.label_suffix = ""


from PIL import Image
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            try:
                img = Image.open(avatar)
                
                # Проверка типа содержимого
                main, sub = avatar.content_type.split('/')
                if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'png']):
                    raise forms.ValidationError('Пожалуйста, используйте изображение в формате JPEG или PNG.')
                
                # Проверка размера файла
                if avatar.size > (20 * 1024 * 1024):  # 20 МБ
                    raise forms.ValidationError('Размер файла аватара не должен превышать 20 МБ.')

                # Проверка соотношения сторон
                width, height = img.size
                aspect_ratio = width / height
                if not (0.5 <= aspect_ratio <= 2.0):
                    raise forms.ValidationError('Соотношение сторон изображения должно быть не более 2:1 и 1:2.')

                # Изменение разрешения изображения, если оно слишком большое
                max_resolution = 2000
                if width > max_resolution or height > max_resolution:
                    output_size = (max_resolution, max_resolution)
                    img.thumbnail(output_size, Image.ANTIALIAS)
                    img.save(avatar, format=img.format)

            except AttributeError:
                pass

        return avatar