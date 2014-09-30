from django import forms
from apps.canvas.models import UserProfile, Picture, Votes, Report


class UserForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = {'terms_conditions'}


class PictureForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = {'pic', 'real_age'}
        widgets = {
            'pic': forms.ImageField.widget(attrs={
                'style': 'margin-bottom: 7px;' +
                         'padding-bottom: 25px;' +
                         'border-bottom: 0px;' +
                         'background-color: #FFFFFF;'
            }),
            'real_age': forms.IntegerField.widget(attrs={
                'min': 1,
                'max': 100,
                'value': 50,
                'placeholder': 'How old were the person in the image?',
                'type': 'range',
                'onchange': 'showValue(this.value)',
                'oninput': 'showValue(this.value)'
            })
        }


class VoteForm(forms.ModelForm):
    class Meta:
        model = Votes
        fields = {'vote'}
        widgets = {
            'vote': forms.NumberInput(attrs={
                'min': 1,
                'max': 100,
                'value': 0,
                'placeholder': 'How old does he/she looks like?',
                'type': 'range',
                'onchange': 'showValue(this.value)',
                'oninput': 'showValue(this.value)'
            })
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = {'detail'}
        widgets = {
            'detail': forms.TextInput(attrs={
                'placeholder': 'Write the reasons of your report'
            })
        }