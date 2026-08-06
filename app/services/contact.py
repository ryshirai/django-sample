from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser

from app.drafts import ContactPayload
from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_contact(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    payload: ContactPayload,
) -> ApplicationDraft:
    """contact セクションを payload で置き換える。"""

    def mutate(data: dict) -> None:
        data["contact"] = {
            "phone": payload.phone,
            "email": payload.email,
            "preferred_method": payload.preferred_method,
            "note": payload.note,
        }

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
