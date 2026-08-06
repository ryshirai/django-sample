from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import IntegrityError, transaction

from app.drafts import CURRENT_SCHEMA_VERSION, empty_draft_data, snapshot_application
from app.models import Application, ApplicationDraft


@transaction.atomic
def create_draft(
    *,
    owner: AbstractBaseUser,
    application_id: UUID | None = None,
) -> ApplicationDraft:
    """新規空 Draft、または既存 Application の snapshot Draft を返す。"""
    if application_id is None:
        return ApplicationDraft.objects.create(
            owner=owner,
            data=empty_draft_data(),
            schema_version=CURRENT_SCHEMA_VERSION,
        )

    existing = (
        ApplicationDraft.objects.owned_by(owner)
        .editing()
        .filter(application_id=application_id)
        .first()
    )
    if existing:
        return existing

    application = (
        Application.objects.select_for_update()
        .owned_by(owner)
        .with_details()
        .get(pk=application_id)
    )
    application.ensure_editable()
    try:
        return ApplicationDraft.objects.create(
            owner=owner,
            application=application,
            data=snapshot_application(application),
            schema_version=CURRENT_SCHEMA_VERSION,
        )
    except IntegrityError:
        # 同時作成で unique に負けた場合は勝者の編集中 Draft を返す。
        return ApplicationDraft.objects.owned_by(owner).editing().get(application=application)


@transaction.atomic
def delete_draft(*, draft_id: UUID, owner: AbstractBaseUser) -> None:
    """編集中 Draft と未採用アップロードを削除する。"""
    draft = ApplicationDraft.objects.for_update().owned_by(owner).editing().get(pk=draft_id)
    files = [(upload.file.storage, upload.file.name) for upload in draft.uploads.all()]
    draft.delete()
    for storage, name in files:
        transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
