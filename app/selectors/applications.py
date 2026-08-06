from django.shortcuts import get_object_or_404

from app.models import Application


def application_list(*, user):
    return Application.objects.visible_to(user).order_by("-updated_at")


def get_application_for_edit(*, application_id, user) -> Application:
    return get_object_or_404(
        Application.objects.visible_to(user).with_details(),
        pk=application_id,
    )
