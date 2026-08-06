from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser

from app.drafts import BasicPayload
from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_basic(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    payload: BasicPayload,
) -> ApplicationDraft:
    """basic セクションを payload で置き換える。"""

    def mutate(data: dict) -> None:
        data["basic"] = {"title": payload.title, "purpose": payload.purpose}

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
