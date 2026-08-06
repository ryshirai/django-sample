from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser

from app.drafts import BudgetItemPayload
from app.models import ApplicationDraft

from .draft_updater import update_draft_data


def update_budget_items(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    budget_items: list[BudgetItemPayload],
) -> ApplicationDraft:
    """budget_items 配列を正規化済み payload で置き換える。"""
    normalized = [
        {
            "row_id": str(item.row_id),
            "source_id": str(item.source_id) if item.source_id else None,
            "description": item.description,
            "amount": item.amount,
            "category": item.category,
        }
        for item in budget_items
    ]

    def mutate(data: dict) -> None:
        data["budget_items"] = normalized

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
