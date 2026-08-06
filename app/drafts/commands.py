from dataclasses import dataclass
from uuid import UUID

from app.models import ApplicationDraft


@dataclass(frozen=True, slots=True)
class MemberCommand:
    row_id: UUID
    source_id: UUID | None
    name: str
    email: str
    role: str


@dataclass(frozen=True, slots=True)
class BudgetItemCommand:
    row_id: UUID
    source_id: UUID | None
    description: str
    amount: int
    category: str


@dataclass(frozen=True, slots=True)
class AttachmentCommand:
    row_id: UUID
    source_id: UUID | None
    label: str
    file_name: str
    storage_name: str


@dataclass(frozen=True, slots=True)
class ApplicationCommand:
    """submit が正式モデルへ書き込む不変の入力束。"""

    title: str
    purpose: str
    postal_code: str
    prefecture: str
    city: str
    address_line: str
    contact_phone: str
    contact_email: str
    preferred_contact_method: str
    contact_note: str
    members: tuple[MemberCommand, ...]
    budget_items: tuple[BudgetItemCommand, ...]
    attachments: tuple[AttachmentCommand, ...]


def command_from_draft(draft: ApplicationDraft) -> ApplicationCommand:
    """検証済み Draft から ApplicationCommand を組み立てる。"""
    data = draft.data
    basic = data["basic"]
    address = data["address"]
    contact = data["contact"]
    return ApplicationCommand(
        title=basic["title"],
        purpose=basic["purpose"],
        postal_code=address["postal_code"],
        prefecture=address["prefecture"],
        city=address["city"],
        address_line=address["address_line"],
        contact_phone=contact["phone"],
        contact_email=contact["email"],
        preferred_contact_method=contact["preferred_method"],
        contact_note=contact.get("note") or "",
        members=tuple(
            MemberCommand(
                row_id=UUID(item["row_id"]),
                source_id=UUID(item["source_id"]) if item.get("source_id") else None,
                name=item["name"],
                email=item["email"],
                role=item["role"],
            )
            for item in data["members"]
        ),
        budget_items=tuple(
            BudgetItemCommand(
                row_id=UUID(item["row_id"]),
                source_id=UUID(item["source_id"]) if item.get("source_id") else None,
                description=item["description"],
                amount=int(item["amount"]),
                category=item["category"],
            )
            for item in data.get("budget_items", [])
        ),
        attachments=tuple(
            AttachmentCommand(
                row_id=UUID(item["row_id"]),
                source_id=UUID(item["source_id"]) if item.get("source_id") else None,
                label=item["label"],
                file_name=item["file_name"],
                storage_name=item["storage_name"],
            )
            for item in data["attachments"]
        ),
    )
