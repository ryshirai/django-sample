from app.drafts import CURRENT_SCHEMA_VERSION, migrate_draft_data
from app.models import ApplicationDraft


def ensure_current_schema(*, draft: ApplicationDraft) -> ApplicationDraft:
    """古い schema_version の data を CURRENT まで進め、必要なら永続化する。"""
    if draft.schema_version >= CURRENT_SCHEMA_VERSION:
        return draft

    draft.data = migrate_draft_data(draft.data, from_version=draft.schema_version)
    draft.schema_version = CURRENT_SCHEMA_VERSION
    draft.save(update_fields=("data", "schema_version", "updated_at"))
    return draft
