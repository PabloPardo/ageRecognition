from django import forms
from apps.canvas.models import Picture, Votes
from tinymce.widgets import TinyMCE


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
            })
        }


class VoteForm(forms.ModelForm):
    class Meta:
        model = Votes
        fields = {'vote'}
        widgets = {
            'vote': forms.NumberInput(attrs={
                'min': '1',
                'max': '90',
                'placeholder': 'How old does he/she looks like?'})
        }


