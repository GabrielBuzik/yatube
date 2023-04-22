from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': ('Post text'),
            'group': ('Group ')
        }
        help_texts = {
            'text': ('Text of the new post '),
            'group': ('Group to which this post will belong ')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': ('Comment text')
        }
        help_texts = {
            'text': ('Comment text')
        }
