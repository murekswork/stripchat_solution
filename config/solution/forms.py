from django import forms

from accounts.models import StripChatUser


class SolutionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=StripChatUser.objects.all(), label="Пользователь для входа"
    )
    username = forms.CharField(max_length=255, label="Пользователь для поиска")
