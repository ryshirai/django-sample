import re
from collections import Counter

from app.errors import ValidationError
from app.messages import VALIDATION_MESSAGES
from app.models import ApplicationMember

POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-?\d{4}$")


def validate_draft(data: dict) -> None:
    """画面をまたぐ整合性を検証する。Model.full_cleanとは責務を分ける。"""
    errors: dict[str, list[str]] = {}
    basic = data.get("basic", {})
    address = data.get("address", {})
    members = data.get("members", [])
    attachments = data.get("attachments", [])

    _required(
        errors, "basic.title", basic.get("title"), VALIDATION_MESSAGES["basic_title_required"]
    )
    _required(
        errors, "basic.purpose", basic.get("purpose"), VALIDATION_MESSAGES["basic_purpose_required"]
    )
    _required(
        errors,
        "address.prefecture",
        address.get("prefecture"),
        VALIDATION_MESSAGES["prefecture_required"],
    )
    _required(errors, "address.city", address.get("city"), VALIDATION_MESSAGES["city_required"])
    _required(
        errors,
        "address.address_line",
        address.get("address_line"),
        VALIDATION_MESSAGES["address_line_required"],
    )

    postal_code = address.get("postal_code", "")
    if not POSTAL_CODE_PATTERN.fullmatch(postal_code):
        errors.setdefault("address.postal_code", []).append(
            VALIDATION_MESSAGES["postal_code_invalid"]
        )

    if not members:
        errors.setdefault("members", []).append(VALIDATION_MESSAGES["member_required"])
    email_counts = Counter(item.get("email", "").casefold() for item in members)
    if any(email and count > 1 for email, count in email_counts.items()):
        errors.setdefault("members", []).append(VALIDATION_MESSAGES["member_email_duplicate"])
    if members and not any(item.get("role") == ApplicationMember.Role.OWNER for item in members):
        errors.setdefault("members", []).append(VALIDATION_MESSAGES["owner_required"])

    member_row_ids = [item.get("row_id") for item in members]
    attachment_row_ids = [item.get("row_id") for item in attachments]
    if len(member_row_ids) != len(set(member_row_ids)):
        errors.setdefault("members", []).append(VALIDATION_MESSAGES["member_row_id_duplicate"])
    if len(attachment_row_ids) != len(set(attachment_row_ids)):
        errors.setdefault("attachments", []).append(
            VALIDATION_MESSAGES["attachment_row_id_duplicate"]
        )
    for item in attachments:
        if not item.get("storage_name"):
            errors.setdefault("attachments", []).append(
                VALIDATION_MESSAGES["attachment_file_required"]
            )
            break

    if errors:
        raise ValidationError(errors=errors)


def _required(errors: dict[str, list[str]], key: str, value, message: str) -> None:
    if not value:
        errors.setdefault(key, []).append(message)
