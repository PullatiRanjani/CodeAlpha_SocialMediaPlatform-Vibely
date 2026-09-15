from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    display_name=models.CharField(max_length=80,blank=True)
    bio=models.TextField(max_length=160,blank=True)
    avatar=models.ImageField(upload_to='avatars/',blank=True,null=True)
    website=models.URLField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.user.username} profile'
    @property
    def name(self): return self.display_name or self.user.get_full_name() or self.user.username

class Follow(models.Model):
    follower=models.ForeignKey(User,on_delete=models.CASCADE,related_name='following_links')
    following=models.ForeignKey(User,on_delete=models.CASCADE,related_name='follower_links')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['follower','following'],name='unique_follow')]
        ordering=['-created_at']

class Post(models.Model):
    author=models.ForeignKey(User,on_delete=models.CASCADE,related_name='posts')
    caption=models.TextField(max_length=2200,blank=True)
    image=models.ImageField(upload_to='posts/',blank=True,null=True)
    video=models.FileField(upload_to='posts/videos/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class Like(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='post_likes')
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='likes')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','post'],name='unique_post_like')]

class Comment(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='comments')
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    text=models.CharField(max_length=600)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['created_at']

class Story(models.Model):
    author=models.ForeignKey(User,on_delete=models.CASCADE,related_name='stories')
    image=models.ImageField(upload_to='stories/images/',blank=True,null=True)
    video=models.FileField(upload_to='stories/videos/',blank=True,null=True)
    caption=models.CharField(max_length=220,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField()
    def save(self,*args,**kwargs):
        if not self.expires_at: self.expires_at=timezone.now()+timedelta(hours=24)
        super().save(*args,**kwargs)
    @property
    def is_active(self): return self.expires_at>timezone.now()
    @property
    def is_video(self): return bool(self.video)
    class Meta: ordering=['-created_at']

class StoryLike(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='story_likes')
    story=models.ForeignKey(Story,on_delete=models.CASCADE,related_name='likes')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','story'],name='unique_story_like')]

class StoryReply(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='story_replies')
    story=models.ForeignKey(Story,on_delete=models.CASCADE,related_name='replies')
    text=models.CharField(max_length=500)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['created_at']

class StoryView(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='story_views')
    story=models.ForeignKey(Story,on_delete=models.CASCADE,related_name='views')
    viewed_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','story'],name='unique_story_view')]

class Notification(models.Model):
    KIND_CHOICES=[('like','liked your post'),('comment','commented on your post'),('follow','started following you'),('story_like','liked your story'),('story_reply','replied to your story')]
    recipient=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
    actor=models.ForeignKey(User,on_delete=models.CASCADE,related_name='sent_notifications')
    kind=models.CharField(max_length=30,choices=KIND_CHOICES)
    post=models.ForeignKey(Post,on_delete=models.CASCADE,null=True,blank=True)
    story=models.ForeignKey(Story,on_delete=models.CASCADE,null=True,blank=True)
    text=models.CharField(max_length=500,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    is_read=models.BooleanField(default=False)
    class Meta: ordering=['-created_at']
