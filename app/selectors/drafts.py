from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from app.models import ApplicationDraft


def editing_draft_list(*, user: AbstractBaseUser) -> QuerySet[ApplicationDraft]:
    """所有者の編集中 Draft 一覧。"""
    return ApplicationDraft.objects.owned_by(user).editing().order_by("-updated_at")


def get_draft_for_edit(*, draft_id: UUID, user: AbstractBaseUser) -> ApplicationDraft:
    """
    所有者スコープの Draft を取得する。見つからなければ 404。

    編集中かどうかはここでは見ない。SUBMITTED などは Service / Model の
    ensure_editable が DomainError にする。
    """
    return get_object_or_404(
        ApplicationDraft.objects.owned_by(user),
        pk=draft_id,
    )
