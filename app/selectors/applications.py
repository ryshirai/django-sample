from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from app.models import Application


def application_list(
    *,
    user: AbstractBaseUser,
    status: str | None = None,
    query: str | None = None,
) -> QuerySet[Application]:
    """所有者の正式申請一覧。任意で状態・申請名で絞り込む。"""
    queryset = Application.objects.owned_by(user)
    if status:
        queryset = queryset.with_status(status)
    if query:
        queryset = queryset.matching_title(query)
    return queryset.order_by("-updated_at")


def get_application_for_edit(*, application_id: UUID, user: AbstractBaseUser) -> Application:
    """編集開始用に Application を取得する。見つからなければ 404。"""
    return get_object_or_404(
        Application.objects.owned_by(user).with_details(),
        pk=application_id,
    )


def get_application_for_owner(*, application_id: UUID, user: AbstractBaseUser) -> Application:
    """所有者向け詳細表示。見つからなければ 404。"""
    return get_object_or_404(
        Application.objects.owned_by(user).with_details().with_history(),
        pk=application_id,
    )


def review_queue() -> QuerySet[Application]:
    """審査対象（申請済み・審査中）の一覧。staff 向け。"""
    return Application.objects.for_review().with_details().order_by("submitted_at")


def get_application_for_review(*, application_id: UUID) -> Application:
    """審査画面用。見つからなければ 404。所有者スコープは掛けない。"""
    return get_object_or_404(
        Application.objects.with_details().with_history(),
        pk=application_id,
    )
