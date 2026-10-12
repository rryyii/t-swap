from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy, reverse
from .models import Channel, Post, Response
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from django.http import HttpResponseRedirect
from .forms import PromptForm, ResponseForm
from asgiref.sync import async_to_sync
from random import choice
from channels.layers import get_channel_layer
from django.core.cache import cache


JOINED_CHANNELS_SESSION_KEY = "joined_channels"


def submissions_open_key(channel_id):
    """
    Cache key that tracks whether a channel's current post accepts responses.
    """
    return f"submissions_open_{channel_id}"


def is_facilitator(user):
    return user.is_authenticated and user.user_type == "facilitator"


def get_owned_channel(request, channel_id):
    """
    Fetches a channel, raising PermissionDenied unless the current user created it.
    """
    channel = get_object_or_404(Channel, pk=channel_id)
    if channel.creator_id != request.user.pk:
        raise PermissionDenied
    return channel


def can_access_channel(request, channel):
    """
    The creator can always enter a channel; everyone else must have joined it with its code.
    """
    if channel.creator_id == request.user.pk:
        return True
    return channel.pk in request.session.get(JOINED_CHANNELS_SESSION_KEY, [])


def ensure_channel_post(channel):
    """
    Gives a channel a default post if it has none (e.g. its post was deleted).
    """
    if channel.post is None:
        channel.post = Post.objects.create(
            facilitator=channel.creator,
            channel_owner=channel,
            prompt="Default prompt for this channel",
            post_date=None,
        )
        channel.save()
    return channel.post


class FacilitatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restricts a view to logged in facilitators.
    """
    def test_func(self):
        return is_facilitator(self.request.user)


def index(request):
    """
    Index function renders and passes relevant context, including current channel,
    current posts, etc to the index page.
    """
    current_channels = Channel.objects.all()
    current_posts = Post.objects.all()
    current_posts_count = Post.objects.all().count()

    context = {
        "current_channels": current_channels,
        "current_posts": current_posts,
        "current_posts_count": current_posts_count,
    }
    return render(request, "thoughtswap/index.html", context=context)


@login_required
@require_POST
def join_channel(request, channel_id):
    """
    Checks the submitted channel code and, if it matches, lets the user into the channel.
    """
    channel = get_object_or_404(Channel, pk=channel_id)
    if request.POST.get("channel_code", "") != channel.channel_code:
        messages.error(request, "Incorrect channel code.")
        return redirect("index")

    joined = request.session.get(JOINED_CHANNELS_SESSION_KEY, [])
    if channel.pk not in joined:
        joined.append(channel.pk)
        request.session[JOINED_CHANNELS_SESSION_KEY] = joined
    return redirect("room", channel_id=channel.pk)


class ChannelListView(ListView):
    """
    ChannelListView class provides baseline ListView functionality.
    """
    model = Channel


class ChannelDetailView(DetailView):
    """
    ChannelDetailView class provides baseline DetailView functionality.
    """
    model = Channel


class ChannelManage(FacilitatorRequiredMixin, ListView):
    """
    ChannelManage class provides baseline ListView functionality for channel management.
    """
    model = Channel
    template_name = "thoughtswap/manage_channels.html"


class ChannelCreate(FacilitatorRequiredMixin, CreateView):
    """
    ChannelCreate class handles the form to create a new Channel.
    """
    model = Channel
    fields = ["channel_name", "channel_code"]

    def form_valid(self, form):
        form.instance.creator = self.request.user
        channel = form.save()
        ensure_channel_post(channel)
        return super().form_valid(form)


class ChannelOwnerMixin(FacilitatorRequiredMixin):
    """
    Limits a channel view to channels created by the current user.
    """
    def get_queryset(self):
        return Channel.objects.filter(creator=self.request.user)


class ChannelDelete(ChannelOwnerMixin, DeleteView):
    """
    ChannelDelete class handles deletion of a Channel according to channel id and name.
    """
    model = Channel
    fields = ["channel_id", "channel_name"]
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("delete-channel", kwargs={"pk": self.object.pk})
            )


class ChannelUpdate(ChannelOwnerMixin, UpdateView):
    """
    ChannelUpdate class handles basic updating of a channel including its name and code.
    """
    model = Channel
    fields = ["channel_name", "channel_code"]


@login_required
def manage_responses(request, channel_id, post_id):
    """
    Manages responses to a channel and current post and passes the relevant context.
    """
    channel = get_owned_channel(request, channel_id)
    post = get_object_or_404(Post, pk=post_id)
    responses = Response.objects.filter(post=post)
    CONTEXT = {
        "channel": channel,
        "post": post,
        "responses": responses,
    }
    return render(request, "thoughtswap/manage_responses.html", context=CONTEXT)


@login_required
def post_create(request):
    """
    Creates a new prompt/post form
    """
    if not is_facilitator(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = PromptForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.facilitator = request.user
            post.save()
            return redirect("manage-channels")
    else:
        form = PromptForm()
    return render(request, "thoughtswap/post_form.html", {"form": form})


@login_required
def delete_saved_post(request, post_id, user_id):
    """
    Removes a post from the current user's saved posts. The post itself is kept.
    """
    if user_id != request.user.pk:
        raise PermissionDenied
    request.user.saved_posts.remove(post_id)
    return redirect("manage-channels")


class PostOwnerMixin(FacilitatorRequiredMixin):
    """
    Limits a post view to posts facilitated by the current user.
    """
    def get_queryset(self):
        return Post.objects.filter(facilitator=self.request.user)


class PostDelete(PostOwnerMixin, DeleteView):
    """
    PostDelete class handles deletion of a Post.
    """
    model = Post
    fields = ["post_id"]
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("delete-post", kwargs={"pk": self.object.pk})
            )


class PostUpdate(PostOwnerMixin, UpdateView):
    """
    PostUpdate handles basic updating of a post, including prompt, participants
    and post date.
    """
    model = Post
    fields = ["prompt", "participants", "post_date"]


@login_required
def save_post(request, post_id, user_id):
    """
    Saves the current post to the current user's saved posts.
    """
    if user_id != request.user.pk or not is_facilitator(request.user):
        raise PermissionDenied
    post = get_object_or_404(Post, pk=post_id)
    request.user.saved_posts.add(post)
    return redirect("manage-channels")


@login_required
def post_view(request, post_id):
    """
    Fetches all relevant responses to a post and then returns it.
    """
    if not is_facilitator(request.user):
        raise PermissionDenied
    post = get_object_or_404(Post, pk=post_id)
    responses = Response.objects.filter(post=post)
    CONTEXT = {
        "post": post,
        "responses": responses,
    }
    return render(request, "thoughtswap/post_detail.html", context=CONTEXT)


@login_required
def room(request, channel_id):
    """
    Handles communication between channels and the main room page.
    Saves submitted prompts and responses, then broadcasts them to the channel's group.
    """
    channel = get_object_or_404(Channel, pk=channel_id)
    if not can_access_channel(request, channel):
        messages.error(request, "Enter the channel code to join this channel.")
        return redirect("index")

    is_owner = channel.creator_id == request.user.pk
    post = ensure_channel_post(channel)

    post_id = post.pk
    post_date = post.post_date.strftime("%Y-%m-%d") if post.post_date else "Unknown"
    facilitator = post.facilitator.username if post.facilitator else "Unknown"

    prompt_form = PromptForm(instance=post)
    response_form = ResponseForm()

    submissions_open = cache.get(submissions_open_key(channel_id), True)
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "prompt" and is_owner:
            prompt_form = PromptForm(request.POST)
            if prompt_form.is_valid():
                new_post = prompt_form.save(commit=False)
                new_post.facilitator = request.user
                new_post.channel_owner = channel
                new_post.post_date = timezone.now()
                new_post.save()

                channel.post = new_post
                channel.save()
                cache.delete(submissions_open_key(channel_id))

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"chat_{channel_id}",
                    {
                        "type": "chat_message",
                        "message": new_post.prompt,
                        "post_id": new_post.pk,
                        "post_date": new_post.post_date.strftime("%Y-%m-%d"),
                        "facilitator": new_post.facilitator.username,
                    },
                )

                return redirect("room", channel_id=channel_id)

        elif form_type == "response" and request.user.user_type == "participant":
            if not submissions_open:
                messages.error(request, "Submissions are closed for this prompt.")
                return redirect("room", channel_id=channel_id)
            response_form = ResponseForm(request.POST)
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.participant = request.user
                response.post = post
                response.response_date = timezone.now()
                response.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"chat_{channel_id}",
                    {
                        "type": "response_message",
                        "message": response.response_content,
                        "message_type": "response",
                        "response_id": response.pk,
                        "response_content": response.response_content,
                    },
                )
                return redirect("room", channel_id=channel_id)

        else:
            raise PermissionDenied

    return render(
        request,
        "thoughtswap/channel_post.html",
        {
            "channel": channel,
            "post": post,
            "room_name": channel_id,
            "form": prompt_form,
            "response_form": response_form,
            "post_id": post_id,
            "post_date": post_date,
            "facilitator": facilitator,
            "is_owner": is_owner,
            "submissions_open": submissions_open,
        },
    )


@login_required
def show_all(request, channel_id):
    """
    Handles sending and receiving all current responses to a post
    by request of the facilitator to the channel.
    """
    channel = get_owned_channel(request, channel_id)
    responses = Response.objects.filter(post=channel.post)
    channel_layer = get_channel_layer()
    response_data = [
        {
            "response_content": response.response_content,
        }
        for response in responses
    ]
    async_to_sync(channel_layer.group_send)(
        f"chat_{channel_id}",
        {
            "type": "show_all_responses",
            "responses": response_data,
        },
    )
    return redirect("room", channel_id=channel_id)


@login_required
def send_random(request, channel_id):
    """
    Fetches all user's channels and then passes random responses to random user's channels.
    """
    channel = get_owned_channel(request, channel_id)
    post = channel.post
    responses = list(Response.objects.filter(post=post))

    if not responses:
        messages.info(request, "There are no responses to send yet.")
        return redirect("room", channel_id=channel_id)

    channel_layer = get_channel_layer()

    user_ids = cache.get(f"users_in_chat_{channel_id}", set())

    for user_id in user_ids:
        selected_response = choice(responses)

        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "random_response",
                "response_content": selected_response.response_content,
            },
        )

    return redirect("room", channel_id=channel_id)


@login_required
def close_submissions(request, channel_id):
    """
    Stops the channel's current post from accepting responses until a new prompt is sent.
    """
    channel = get_owned_channel(request, channel_id)
    cache.set(submissions_open_key(channel.pk), False, timeout=None)
    return redirect("room", channel_id=channel_id)
