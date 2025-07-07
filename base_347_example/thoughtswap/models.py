from django.db import models
from django.urls import reverse
from base_347_example.users.models import User
from django.utils import timezone

class Response(models.Model):
    """
    Response class defines the properties of Response that is related to a relevant Post.
    """
    response_id = models.AutoField(primary_key=True)
    participant = models.ForeignKey(User, related_name='responses', on_delete=models.CASCADE)
    response_content = models.TextField(default="No current response set")
    response_date = models.DateField()
    post = models.ForeignKey('Post', on_delete=models.CASCADE, blank=True, null=True, related_name='responses')
    
    def __str__(self):
        return f"Response {self.response_id} from {self.participant}"


class Post(models.Model):
    """
    Post class defines the properties for a channel's post.
    """
    post_id = models.AutoField(primary_key=True)
    channel_owner = models.ForeignKey("Channel", related_name="owner", on_delete=models.CASCADE, null=True, blank=True)
    prompt = models.TextField(default="No current prompt set")
    participants = models.ManyToManyField(User, related_name="participated_posts")
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="facilitated_posts") 
    post_date = models.DateField(null=True, blank=True, default=timezone.now)

    class Meta:
        ordering = ["post_date"]
        
    def get_absolute_url(self):
        channel = self.channels.first()
        if channel:
            return reverse('channel-detail', args=[str(channel.channel_id)])
        return reverse('index')

    def __str__(self):
        return f"Post {self.post_id} /  {self.prompt} / created by {self.facilitator}"


class Channel(models.Model):
    """
    Channel class defines the properties for a unique Channel that is only created by Facilitators.
    """
    channel_id = models.AutoField(primary_key=True)
    post = models.OneToOneField(Post, related_name="channels", on_delete=models.SET_NULL, null=True)
    channel_name = models.CharField(max_length=255, default="New Channel")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_channels") 
    participants = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="participating_channels")
    channel_date = models.DateField(null=True, blank=True, default=timezone.now)
    channel_code = models.CharField(max_length=10, default="Code")
    
    class Meta:
        ordering = ["channel_date"]
        
    def get_absolute_url(self):
        return reverse('room', args=[str(self.channel_id)])

    def __str__(self):
        return f"{self.channel_name}"