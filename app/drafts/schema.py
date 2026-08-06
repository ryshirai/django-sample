import uuid
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from app.models import Application

from .types import DraftData

CURRENT_SCHEMA_VERSION = 1

# from_version -> その版から +1 へ進める変換。
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


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
        "members": [],
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
