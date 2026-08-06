import uuid
from typing import Any

from app.models import Application

CURRENT_SCHEMA_VERSION = 1


def empty_draft_data() -> dict[str, Any]:
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


def snapshot_application(application: Application) -> dict[str, Any]:
    """編集開始時に一度だけ正式データをDraft形式へ写像する。"""
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
