from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.shortcuts import get_object_or_404

from app.models import ApplicationDraft


def editing_draft_list(*, user: AbstractBaseUser):
    return ApplicationDraft.objects.owned_by(user).editing().order_by("-updated_at")


def get_draft_for_edit(*, draft_id: UUID, user: AbstractBaseUser) -> ApplicationDraft:
    """編集可能な Draft を取得する。見つからなければ 404。"""
    return get_object_or_404(
        ApplicationDraft.objects.owned_by(user).editing(),
        pk=draft_id,
    )
