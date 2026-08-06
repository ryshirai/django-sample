from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_address(
    *,
    draft_id,
    owner,
    expected_revision: int,
    postal_code: str,
    prefecture: str,
    city: str,
    address_line: str,
) -> ApplicationDraft:
    def mutate(data: dict) -> None:
        data["address"] = {
            "postal_code": postal_code,
            "prefecture": prefecture,
            "city": city,
            "address_line": address_line,
        }

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
