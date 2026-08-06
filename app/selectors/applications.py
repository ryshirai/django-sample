from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.shortcuts import get_object_or_404

from app.models import Application


def application_list(*, user: AbstractBaseUser):
    return Application.objects.owned_by(user).order_by("-updated_at")


def get_application_for_edit(*, application_id: UUID, user: AbstractBaseUser) -> Application:
    return get_object_or_404(
        Application.objects.owned_by(user).with_details(),
        pk=application_id,
    )
