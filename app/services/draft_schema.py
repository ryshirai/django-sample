from django.utils import timezone

from app.drafts import CURRENT_SCHEMA_VERSION, migrate_draft_data
from app.models import ApplicationDraft


def ensure_current_schema(*, draft: ApplicationDraft) -> ApplicationDraft:
    """古い schema_version の data を CURRENT まで進め、必要なら永続化する。"""
    while draft.schema_version < CURRENT_SCHEMA_VERSION:
        source_version = draft.schema_version
        migrated_data = migrate_draft_data(draft.data, from_version=source_version)
        updated_at = timezone.now()
        updated = ApplicationDraft.objects.filter(
            pk=draft.pk,
            schema_version=source_version,
        ).update(
            data=migrated_data,
            schema_version=CURRENT_SCHEMA_VERSION,
            updated_at=updated_at,
        )
        if updated == 1:
            draft.data = migrated_data
            draft.schema_version = CURRENT_SCHEMA_VERSION
            draft.updated_at = updated_at
            return draft

        # 別リクエストが先に移行・更新した場合は、その内容を正として読み直す。
        draft.refresh_from_db()
    return draft
