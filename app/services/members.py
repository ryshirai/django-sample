from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser

from app.drafts import MemberPayload
from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_members(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    members: list[MemberPayload],
) -> ApplicationDraft:
    """members 配列を正規化済み payload で置き換える。"""
    normalized = [
        {
            "row_id": str(item.row_id),
            "source_id": str(item.source_id) if item.source_id else None,
            "name": item.name,
            "email": item.email,
            "role": item.role,
        }
        for item in members
    ]

    def mutate(data: dict) -> None:
        data["members"] = normalized

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
