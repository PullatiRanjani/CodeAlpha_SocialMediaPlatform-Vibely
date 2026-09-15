from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Post, Story, Comment


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False, label='Name')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('caption', 'image', 'video')
        widgets = {
            'caption': forms.Textarea(
                attrs={'rows': 5, 'placeholder': 'Write a caption or share a thought…'}
            ),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'video': forms.ClearableFileInput(
                attrs={'accept': 'video/mp4,video/webm,video/quicktime,video/x-m4v,video/x-msvideo,video/x-matroska'}
            ),
        }

    def clean(self):
        data = super().clean()
        caption = (data.get('caption') or '').strip()
        image = data.get('image')
        video = data.get('video')

        if not caption and not image and not video:
            raise forms.ValidationError('Add a photo, video, or write something before posting.')

        if image and video:
            raise forms.ValidationError('Choose either a photo or a video, not both.')

        if video:
            allowed = ('.mp4', '.webm', '.mov', '.m4v', '.avi', '.mkv')
            if not video.name.lower().endswith(allowed):
                raise forms.ValidationError('Post video must be MP4, WEBM, MOV, M4V, AVI or MKV.')
            if video.size > 50 * 1024 * 1024:
                raise forms.ValidationError('Video size must be 50 MB or less.')

        return data


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ('image', 'video', 'caption')
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Add a caption (optional)'})
        }

    def clean(self):
        data = super().clean()
        image = data.get('image')
        video = data.get('video')
        if not image and not video:
            raise forms.ValidationError('Choose an image or a video for your story.')
        if image and video:
            raise forms.ValidationError('Choose either an image or a video, not both.')
        if video and not video.name.lower().endswith(('.mp4', '.webm', '.mov', '.m4v')):
            raise forms.ValidationError('Story video must be MP4, WEBM, MOV or M4V.')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.TextInput(
                attrs={'placeholder': 'Add a comment…', 'autocomplete': 'off'}
            )
        }


class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(max_length=80, required=False, label='Name')
    remove_avatar = forms.BooleanField(required=False, label='Remove current photo')

    class Meta:
        model = Profile
        fields = ('display_name', 'bio', 'avatar', 'website')
        widgets = {
            'bio': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Tell people a little about you…'}
            )
        }


class LoginForm(forms.Form):
    username = forms.CharField(label='Username or email')
    password = forms.CharField(widget=forms.PasswordInput)
