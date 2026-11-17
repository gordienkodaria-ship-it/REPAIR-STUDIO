from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    User,
    RepairRequest,
    RepairComment,
    Service,
    Part,
    PartUsage,
)


class ClientRegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
        ]

        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone': 'Номер телефона',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT

        if commit:
            user.save()

        return user



class RepairStatusForm(forms.ModelForm):

    class Meta:
        model = RepairRequest
        fields = ['status', 'work_cost']

        labels = {
            'status': 'Новый статус',
            'work_cost': 'Стоимость выполненных работ (₽)',
        }

        widgets = {
            'work_cost': forms.NumberInput(attrs={
                'min': 0,
                'step': '0.01',
                'placeholder': 'Введите стоимость ремонта',
            }),
        }


class RepairCommentForm(forms.ModelForm):

    class Meta:
        model = RepairComment
        fields = ['text']

        labels = {
            'text': 'Комментарий',
        }

        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Введите комментарий...'
            })
        }


class RepairRequestForm(forms.ModelForm):

    class Meta:
        model = RepairRequest
        fields = [
            'device_type',
            'description',
            'service',
            'photo',
        ]

        labels = {
            'device_type': 'Тип устройства',
            'description': 'Описание неисправности',
            'service': 'Выберите услугу',
            'photo': 'Фотография устройства',
        }

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Опишите неисправность...'
            })
        }


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
        ]

        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone': 'Номер телефона',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Введите логин'
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Введите фамилию'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Введите электронную почту'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+7 (___) ___-__-__'
            }),
        }


# Форма назначения мастера

class AssignMasterForm(forms.ModelForm):

    master = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.MASTER),
        empty_label='Выберите мастера',
        label='Ответственный мастер',
        required=False
    )

    class Meta:
        model = RepairRequest
        fields = ['master']


# Форма создания мастера

class MasterCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
        ]

        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone': 'Телефон',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MASTER

        if commit:
            user.save()

        return user


# Форма управления услугами

class ServiceForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = [
            'name',
            'description',
            'price',
            'is_active',
        ]

        labels = {
            'name': 'Название услуги',
            'description': 'Описание',
            'price': 'Стоимость',
            'is_active': 'Услуга активна',
        }

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Описание услуги...'
            })
        }


# Форма управления запчастями

class PartForm(forms.ModelForm):

    class Meta:
        model = Part
        fields = [
            'name',
            'description',
            'quantity',
            'unit_price',
            'min_quantity',
        ]

        labels = {
            'name': 'Название запчасти',
            'description': 'Описание',
            'quantity': 'Количество на складе',
            'unit_price': 'Цена за единицу',
            'min_quantity': 'Минимальный остаток',
        }

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Описание запчасти...'
            })
        }

class PartUsageForm(forms.ModelForm):
    class Meta:
        model = PartUsage
        fields = ['part', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['part'].queryset = Part.objects.filter(quantity__gt=0)
