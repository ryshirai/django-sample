from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_basic(
    *,
    draft_id,
    owner,
    expected_revision: int,
    title: str,
    purpose: str,
) -> ApplicationDraft:
    def mutate(data: dict) -> None:
        data["basic"] = {"title": title, "purpose": purpose}

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
