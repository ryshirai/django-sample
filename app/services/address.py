from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser

from app.drafts import AddressPayload
from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_address(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    payload: AddressPayload,
) -> ApplicationDraft:
    """address セクションを payload で置き換える。"""

    def mutate(data: dict) -> None:
        data["address"] = {
            "postal_code": payload.postal_code,
            "prefecture": payload.prefecture,
            "city": payload.city,
            "address_line": payload.address_line,
        }

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
