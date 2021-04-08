from django import forms
from django.forms import ModelForm, Textarea

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            "group": "Группа",
            "text": "Текст публикации",
            "image": "Изображение",
        }

        help_texts = {
            "group": "Группа, в которой будет опубликован пост",
            "text": "Ваши чувства, мысли и эмоции",
            "image": "Ваше изображение",
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {"text": "Комментарий"}
        widgets = {
            "text": Textarea(attrs={"rows": 2}),
        }
        help_texts = {
            "text": "Ваш прекрасный комментарий",
        }
