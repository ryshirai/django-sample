from app.drafts.types import AttachmentFormInitial
from app.models import ApplicationDraft

from .steps import STEPS


def draft_page_context(*, draft: ApplicationDraft, current_step: str) -> dict:
    """テンプレート共通の draft / ステップ表示データ。"""
    return {
        "draft": draft,
        "current_step": current_step,
        "steps": [(step.key, step.label) for step in STEPS],
    }


def member_initial(draft: ApplicationDraft) -> list[dict]:
    """MemberFormSet 用 initial。"""
    return list(draft.data.get("members", []))


def attachment_initial(draft: ApplicationDraft) -> list[AttachmentFormInitial]:
    """AttachmentFormSet 用 initial（ファイル本体は existing_file_name のみ）。"""
    return [
        {
            "row_id": item["row_id"],
            "source_id": item.get("source_id"),
            "label": item["label"],
            "existing_file_name": item.get("file_name", ""),
        }
        for item in draft.data.get("attachments", [])
    ]
