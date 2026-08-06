from collections import Counter

from app.errors import ValidationError
from app.models import ApplicationMember
from app.rules import POSTAL_CODE_PATTERN, ValidationCode

from .types import DraftData


def validate_draft(data: DraftData | dict) -> None:
    """画面横断の必須・重複・行IDを検証し、失敗時はコード付き ValidationError を投げる。"""
    errors: dict[str, list[str]] = {}
    basic = data.get("basic", {})
    address = data.get("address", {})
    members = data.get("members", [])
    attachments = data.get("attachments", [])

    _required(errors, "basic.title", basic.get("title"), ValidationCode.BASIC_TITLE_REQUIRED)
    _required(errors, "basic.purpose", basic.get("purpose"), ValidationCode.BASIC_PURPOSE_REQUIRED)
    _required(
        errors,
        "address.prefecture",
        address.get("prefecture"),
        ValidationCode.PREFECTURE_REQUIRED,
    )
    _required(errors, "address.city", address.get("city"), ValidationCode.CITY_REQUIRED)
    _required(
        errors,
        "address.address_line",
        address.get("address_line"),
        ValidationCode.ADDRESS_LINE_REQUIRED,
    )

    postal_code = address.get("postal_code", "")
    if not POSTAL_CODE_PATTERN.fullmatch(postal_code or ""):
        errors.setdefault("address.postal_code", []).append(ValidationCode.POSTAL_CODE_INVALID)

    if not members:
        errors.setdefault("members", []).append(ValidationCode.MEMBER_REQUIRED)
    email_counts = Counter(item.get("email", "").casefold() for item in members)
    if any(email and count > 1 for email, count in email_counts.items()):
        errors.setdefault("members", []).append(ValidationCode.MEMBER_EMAIL_DUPLICATE)
    if members and not any(item.get("role") == ApplicationMember.Role.OWNER for item in members):
        errors.setdefault("members", []).append(ValidationCode.OWNER_REQUIRED)

    member_row_ids = [item.get("row_id") for item in members]
    attachment_row_ids = [item.get("row_id") for item in attachments]
    if len(member_row_ids) != len(set(member_row_ids)):
        errors.setdefault("members", []).append(ValidationCode.MEMBER_ROW_ID_DUPLICATE)
    if len(attachment_row_ids) != len(set(attachment_row_ids)):
        errors.setdefault("attachments", []).append(ValidationCode.ATTACHMENT_ROW_ID_DUPLICATE)
    for item in attachments:
        if not item.get("storage_name"):
            errors.setdefault("attachments", []).append(ValidationCode.ATTACHMENT_FILE_REQUIRED)
            break

    if errors:
        raise ValidationError(errors=errors)


def _required(errors: dict[str, list[str]], key: str, value, code: str) -> None:
    if not value:
        errors.setdefault(key, []).append(code)
