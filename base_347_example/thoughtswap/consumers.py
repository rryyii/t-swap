import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from .models import Channel
from .views import JOINED_CHANNELS_SESSION_KEY


@database_sync_to_async
def can_join_room(user, session, room_name):
    """
    Mirrors views.can_access_channel: the creator, or a user who joined with the channel code.
    """
    channel = Channel.objects.filter(pk=room_name).first()
    if channel is None:
        return False
    if channel.creator_id == user.pk:
        return True
    return channel.pk in session.get(JOINED_CHANNELS_SESSION_KEY, [])


class ChatConsumer(AsyncWebsocketConsumer):
    """
    A basic chat consumer that connects, disconnects, and provides handling for messages sent through
    the relevant channels.
    """
    async def connect(self):
        """
        Connects the current user to two different channels including a user specific channel
        and a channel relevant to the joined Channel room.
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user_id = self.scope["user"].id

        self.user_group_name = f"user_{self.user_id}"
        self.room_group_name = f"chat_{self.room_name}"

        user = self.scope["user"]
        if not user.is_authenticated or not await can_join_room(
            user, self.scope.get("session", {}), self.room_name
        ):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

        connected_users = cache.get(f"users_in_{self.room_group_name}", set())
        connected_users.add(self.user_id)
        cache.set(f"users_in_{self.room_group_name}", connected_users, timeout=3600)

    async def disconnect(self, close_code):
        """
        Disconnects and removes the current user from their currently joined groups
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

        connected_users = cache.get(f"users_in_{self.room_group_name}", set())
        connected_users.discard(self.user_id)
        cache.set(f"users_in_{self.room_group_name}", connected_users, timeout=3600)

    async def receive(self, text_data):
        """
        Messages sent by clients are ignored. Prompts and responses are saved and validated
        by the room view, which then broadcasts them to the group.
        """

    async def chat_message(self, event):
        """
        Defines a chat message response.
        """
        message = event["message"]
        post_id = event["post_id"]
        post_date = event["post_date"]
        facilitator = event["facilitator"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "post_id": post_id,
                    "post_date": post_date,
                    "facilitator": facilitator,
                    "form_type": "prompt_form",
                }
            )
        )

    async def show_all_responses(self, event):
        """
        Defines a message to show all relevant responses to a Post.
        """
        responses = event["responses"]
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "show_all_responses",
                    "responses": responses,
                }
            )
        )

    async def response_message(self, event):
        """
        Defines a response message type and sends relevant information.
        """
        message = event["message"]
        message_type = event["message_type"]
        response_id = event["response_id"]
        response_content = event["response_content"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "message_type": message_type,
                    "response_id": response_id,
                    "response_content": response_content,
                }
            )
        )

    async def random_response(self, event):
        """
        Defines a message type for a random response to send to a random user currently
        connected to the relevant channel.
        """
        response_content = event["response_content"]
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "random_response",
                    "response_content": response_content,
                }
            )
        )
