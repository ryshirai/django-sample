"""Draft JSON とステップ更新 payload の型。"""

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict
from uuid import UUID


class BasicSection(TypedDict):
    title: str
    purpose: str


class AddressSection(TypedDict):
    postal_code: str
    prefecture: str
    city: str
    address_line: str


class ContactSection(TypedDict):
    phone: str
    email: str
    preferred_method: str
    note: str


class MemberRow(TypedDict):
    row_id: str
    source_id: str | None
    name: str
    email: str
    role: str


class BudgetItemRow(TypedDict):
    row_id: str
    source_id: str | None
    description: str
    amount: int
    category: str


class AttachmentRow(TypedDict):
    row_id: str
    source_id: str | None
    label: str
    file_name: str
    storage_name: str
    draft_upload_id: str | None


class DraftData(TypedDict):
    basic: BasicSection
    address: AddressSection
    contact: ContactSection
    members: list[MemberRow]
    budget_items: list[BudgetItemRow]
    attachments: list[AttachmentRow]


@dataclass(frozen=True, slots=True)
class BasicPayload:
    title: str
    purpose: str


@dataclass(frozen=True, slots=True)
class AddressPayload:
    postal_code: str
    prefecture: str
    city: str
    address_line: str


@dataclass(frozen=True, slots=True)
class ContactPayload:
    phone: str
    email: str
    preferred_method: str
    note: str


@dataclass(frozen=True, slots=True)
class MemberPayload:
    row_id: UUID
    source_id: UUID | None
    name: str
    email: str
    role: str


@dataclass(frozen=True, slots=True)
class BudgetItemPayload:
    row_id: UUID
    source_id: UUID | None
    description: str
    amount: int
    category: str


@dataclass(frozen=True, slots=True)
class AttachmentPayload:
    row_id: UUID
    source_id: UUID | None
    label: str
    file: Any | None
    existing_file_name: str
    delete: bool = False


class AttachmentFormInitial(TypedDict):
    row_id: str
    source_id: NotRequired[str | None]
    label: str
    existing_file_name: str
