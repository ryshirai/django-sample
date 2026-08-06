from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_members(
    *,
    draft_id,
    owner,
    expected_revision: int,
    members: list[dict],
) -> ApplicationDraft:
    normalized = [
        {
            "row_id": str(item["row_id"]),
            "source_id": str(item["source_id"]) if item.get("source_id") else None,
            "name": item["name"],
            "email": item["email"],
            "role": item["role"],
        }
        for item in members
        if not item.get("DELETE")
    ]

    def mutate(data: dict) -> None:
        data["members"] = normalized

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
