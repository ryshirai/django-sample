from app.models import ApplicationDraft

STEPS = (
    ("basic", "基本情報"),
    ("address", "住所"),
    ("members", "担当者"),
    ("attachments", "添付"),
    ("confirm", "確認"),
)


def draft_page_context(*, draft: ApplicationDraft, current_step: str) -> dict:
    return {
        "draft": draft,
        "current_step": current_step,
        "steps": STEPS,
    }


def member_initial(draft: ApplicationDraft) -> list[dict]:
    return list(draft.data.get("members", []))


def attachment_initial(draft: ApplicationDraft) -> list[dict]:
    return [
        {
            "row_id": item["row_id"],
            "source_id": item.get("source_id"),
            "label": item["label"],
            "existing_file_name": item.get("file_name", ""),
        }
        for item in draft.data.get("attachments", [])
    ]
