import uuid
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from app.models import Application

from .types import DraftData

CURRENT_SCHEMA_VERSION = 2


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """v1 Draft に contact / budget_items を足して v2 にする。"""
    migrated = deepcopy(data)
    migrated.setdefault(
        "contact",
        {"phone": "", "email": "", "preferred_method": "", "note": ""},
    )
    migrated.setdefault("budget_items", [])
    return migrated


# from_version -> その版から +1 へ進める変換。
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    1: _migrate_v1_to_v2,
}


def empty_draft_data() -> DraftData:
    """新規 Draft 用の空 JSON。"""
    return {
        "basic": {"title": "", "purpose": ""},
        "address": {
            "postal_code": "",
            "prefecture": "",
            "city": "",
            "address_line": "",
        },
        "contact": {
            "phone": "",
            "email": "",
            "preferred_method": "",
            "note": "",
        },
        "members": [],
        "budget_items": [],
        "attachments": [],
    }


def snapshot_application(application: Application) -> DraftData:
    """正式 Application を Draft JSON へ写像する。"""
    return {
        "basic": {
            "title": application.title,
            "purpose": application.purpose,
        },
        "address": {
            "postal_code": application.postal_code,
            "prefecture": application.prefecture,
            "city": application.city,
            "address_line": application.address_line,
        },
        "contact": {
            "phone": application.contact_phone,
            "email": application.contact_email,
            "preferred_method": application.preferred_contact_method,
            "note": application.contact_note,
        },
        "members": [
            {
                "row_id": str(uuid.uuid4()),
                "source_id": str(member.id),
                "name": member.name,
                "email": member.email,
                "role": member.role,
            }
            for member in application.members.all()
        ],
        "budget_items": [
            {
                "row_id": str(uuid.uuid4()),
                "source_id": str(item.id),
                "description": item.description,
                "amount": item.amount,
                "category": item.category,
            }
            for item in application.budget_items.all()
        ],
        "attachments": [
            {
                "row_id": str(uuid.uuid4()),
                "source_id": str(attachment.id),
                "label": attachment.label,
                "file_name": attachment.original_name,
                "storage_name": attachment.file.name,
                "draft_upload_id": None,
            }
            for attachment in application.attachments.all()
        ],
    }


def migrate_draft_data(data: dict[str, Any], *, from_version: int) -> DraftData:
    """from_version の data を CURRENT_SCHEMA_VERSION まで進める。"""
    version = from_version
    migrated = deepcopy(data)
    while version < CURRENT_SCHEMA_VERSION:
        migrator = _MIGRATIONS.get(version)
        if migrator is None:
            break
        migrated = migrator(migrated)
        version += 1
    return migrated  # type: ignore[return-value]
