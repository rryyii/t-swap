from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy, reverse
from .models import Channel, Post, Response
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.http import HttpResponseRedirect
from base_347_example.users.models import User
from .forms import PromptForm, ResponseForm
from asgiref.sync import async_to_sync
from random import choice
from channels.layers import get_channel_layer
from django.core.cache import cache


def index(request):
    """
    Index function renders and passes relevant context, including current channel,
    current posts, etc to the index page.
    """
    current_channels = Channel.objects.all()
    current_posts = Post.objects.all()
    current_posts_count = Post.objects.all().count()

    context = {
        "current_posts": current_posts,
        "current_posts_count": current_posts_count,
        "current_channels": current_channels,
    }
    return render(request, "thoughtswap/index.html", context=context)


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


class ChannelManage(ListView):
    """
    ChannelManage class provides baseline ListView functionality for channel management.
    """
    model = Channel
    template_name = "thoughtswap/manage_channels.html"


class ChannelCreate(CreateView):
    """
    ChannelCreate class handles the form to create a new Channel.
    """
    model = Channel
    fields = ["channel_name", "channel_code"]

    def form_valid(self, form):
        user = self.request.user
        if user:
            form.instance.creator = user
        else:
            return redirect("index")

        channel = form.save()

        default_post = Post.objects.create(
            facilitator=user, prompt="Default prompt for this channel", post_date=None
        )
        channel.post = default_post
        channel.save()

        return super().form_valid(form)


class ChannelDelete(DeleteView):
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


class ChannelUpdate(UpdateView):
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
    channel = get_object_or_404(Channel, pk=channel_id)
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
    if request.method == "POST":
        form = PromptForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect()
    else:
        form = PromptForm()
    return render(request, "channel_post.html", {"form": form})


@login_required
def delete_saved_post(request, post_id, user_id):
    """
    Deletes a user's saved post.
    """
    user = get_object_or_404(User, pk=user_id)
    user.saved_posts.filter(pk=post_id).delete()
    return render(request, "thoughtswap/manage_channels.html")


class PostDelete(DeleteView):
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


class PostUpdate(UpdateView):
    """
    PostUpdate handles basic updating of a post, including prompt, participants,
    responses, and post date.
    """
    model = Post
    fields = ["prompt", "participants", "responses", "post_date"]


@login_required
def save_post(request, post_id, user_id):
    """
    Saves the current post to a user's saved posts.
    """
    post = get_object_or_404(Post, pk=post_id)
    user = get_object_or_404(User, pk=user_id)
    user.saved_posts.add(post)
    return render(request, "thoughtswap/manage_channels.html")


@login_required
def post_view(request, post_id):
    """
    Fetches all relevant responses to a post and then returns it.
    """
    post = get_object_or_404(Post, pk=post_id)
    responses = []
    for response in Response.objects.all():
        if response.post == post:
            responses.append(response)
    CONTEXT = {
        "post": post,
        "responses": responses,
    }
    return render(request, "thoughtswap/post_detail.html", context=CONTEXT)


@login_required
def room(request, channel_id):
    """
    Handles communication between channels and the main room page.
    Uses the consumers file to deal with forms and sending them to their relevant channel.
    """
    channel = get_object_or_404(Channel, pk=channel_id)
    post = channel.post

    post_id = post.pk
    post_date = post.post_date.strftime("%Y-%m-%d") if post.post_date else "Unknown"
    facilitator = post.facilitator.username if post.facilitator else "Unknown"

    prompt_form = PromptForm(instance=post)
    response_form = ResponseForm()

    submission_status = cache.get("submission_status", False)
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "prompt" and request.user.user_type == "facilitator":
            prompt_form = PromptForm(request.POST)
            if prompt_form.is_valid():
                new_post = prompt_form.save(commit=False)
                new_post.facilitator = request.user
                new_post.channel_owner = channel
                new_post.post_date = timezone.now()
                new_post.save()

                channel.post = new_post
                channel.save()

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
            response_form = ResponseForm(request.POST)
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.participant = request.user
                response.post = post
                response.response_date = timezone.now()
                response.save()
                return redirect("room", channel_id=channel_id)

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
            "submission_status": submission_status,
        },
    )


@login_required
def show_all(request, channel_id):
    """
    Handles sending and receiving all current responses to a post
    by request of the facilitator to the channel.
    """
    channel = get_object_or_404(Channel, pk=channel_id)
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
    channel = get_object_or_404(Channel, pk=channel_id)
    post = channel.post
    responses = list(Response.objects.filter(post=post))

    if not responses:
        return render(
            request,
            "thoughtswap/channel_post.html",
            {
                "channel": channel,
                "post": post,
            },
        )

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


def close_submissions(request, channel_id):
    cache.set("response_status", False)
    return render(
        request, "thoughtswap/channel_post.html", context={channel_id: channel_id}
    )
