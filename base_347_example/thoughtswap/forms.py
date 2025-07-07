from django import forms
from .models import Post, Response

class PromptForm(forms.ModelForm):
    """
    PromptForm class defines a model form for a new Prompt/Post using the Post model
    """
    class Meta:
        model = Post
        fields = ['prompt']


class ResponseForm(forms.ModelForm):
    """
    ResponseForm class defines a model form for a new Response to append to a Post using the
    Response model.
    """
    class Meta:
        model = Response
        fields = ['response_content']
        