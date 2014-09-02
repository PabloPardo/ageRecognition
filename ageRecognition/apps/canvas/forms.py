from django import forms


class PictureForm(forms.Form):
    pic = forms.ImageField()
    pic.widget.attrs.update({'style': 'margin-bottom: 7px;' +
                                      'padding-bottom: 25px;' +
                                      'border-bottom: 0px;' +
                                      'background-color: #FFFFFF;'})


class VoteForm(forms.Form):
    vote = forms.NumberInput(attrs={'min': '1',
                                    'max': '90',
                                    'placeholder': 'How old does he/she looks like?'})


