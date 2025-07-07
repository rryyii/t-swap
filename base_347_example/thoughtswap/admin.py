from django.contrib import admin
from .models import Channel, Post, Response
# Register your models here.
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_id', 'channel_name', 'creator', 'post', 'channel_date')
    fields = ['channel_name', 'creator', 'post', 'channel_code', 'channel_date']

admin.site.register(Channel, ChannelAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'facilitator', 'channel_owner', 'prompt','post_date')
    fields = ['participants', 'facilitator','channel_owner', 'prompt', 'post_date']
admin.site.register(Post, PostAdmin)

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('post', 'response_id', 'participant', 'response_content','response_date')
    fields = ['post', 'participant', 'response_content','response_date']
admin.site.register(Response, ResponseAdmin)

