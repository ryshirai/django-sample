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
class AttachmentCommand:
    row_id: UUID
    source_id: UUID | None
    label: str
    file_name: str
    storage_name: str


@dataclass(frozen=True, slots=True)
class ApplicationCommand:
    title: str
    purpose: str
    postal_code: str
    prefecture: str
    city: str
    address_line: str
    members: tuple[MemberCommand, ...]
    attachments: tuple[AttachmentCommand, ...]


def command_from_draft(draft: ApplicationDraft) -> ApplicationCommand:
    data = draft.data
    basic = data["basic"]
    address = data["address"]
    return ApplicationCommand(
        title=basic["title"],
        purpose=basic["purpose"],
        postal_code=address["postal_code"],
        prefecture=address["prefecture"],
        city=address["city"],
        address_line=address["address_line"],
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
