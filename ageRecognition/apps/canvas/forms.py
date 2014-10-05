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
                'onchange': 'showValue("range_game_1", this.value)',
                'oninput': 'showValue("range_game_1", this.value)'
            })
        }


class ReportForm(forms.Form):
    REPORT_CHOICES = [(0, 'Doesn\'t appear any face'),
                      (1, 'There are more than one face'),
                      (2, 'Unethical'),
                      (3, 'Other')]

    other = forms.CharField()
    other.widget = forms.TextInput(attrs={'placeholder': 'Write the reasons of your report',
                                          'style': 'width: 200px', 'width': '200px'})

    options = forms.ChoiceField(choices=REPORT_CHOICES, widget=forms.RadioSelect())
