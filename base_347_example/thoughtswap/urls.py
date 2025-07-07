from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
]

urlpatterns += [
    path(
        "facilitator_dashboard/", views.ChannelManage.as_view(), name="manage-channels"
    ),
    path(
        "facilitator_dashboard/create/",
        views.ChannelCreate.as_view(),
        name="create-channel",
    ),
    path(
        "facilitator_dashboard/delete/<int:pk>",
        views.ChannelDelete.as_view(),
        name="delete-channel",
    ),
    path(
        "facilitator_dashboard/edit/<int:pk>/",
        views.ChannelUpdate.as_view(),
        name="edit-channel",
    ),
    path(
        "facilitator_dashboard/archive/post/<int:post_id>",
        views.post_view,
        name="post-archive-detail",
    ),
    path(
        "facilitator_dashboard/archive/post/<int:post_id>/<int:user_id>",
        views.delete_saved_post,
        name="delete-saved-post",
    ),
]

urlpatterns += [
    path("channel/", views.index, name="index"),
    path("channel/<int:channel_id>/", views.room, name="room"),
    path("channel/create/", views.post_create, name="create-post"),
    path(
        "channel/manage/<int:channel_id>/<int:post_id>",
        views.manage_responses,
        name="manage-responses",
    ),
    path(
        "channel/save_post/<int:post_id>/<int:user_id>",
        views.save_post,
        name="save-post",
    ),
    path("channel/<int:channel_id>", views.show_all, name="show-all"),
    path("channel/send-random/<int:channel_id>", views.send_random, name="send-random"),
    path(
        "channel/close/<int:channel_id>",
        views.close_submissions,
        name="close-submissions",
    ),
]
