from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from app.models import Application


def application_list(*, user: AbstractBaseUser) -> QuerySet[Application]:
    """所有者の正式申請一覧。"""
    return Application.objects.owned_by(user).order_by("-updated_at")


def get_application_for_edit(*, application_id: UUID, user: AbstractBaseUser) -> Application:
    """編集開始用に Application を取得する。見つからなければ 404。"""
    return get_object_or_404(
        Application.objects.owned_by(user).with_details(),
        pk=application_id,
    )
