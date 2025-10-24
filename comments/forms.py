from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder': 'Tulis komentar/ulasan kamu...'}),
            'rating': forms.NumberInput(attrs={'min':1, 'max':5}),
        }
