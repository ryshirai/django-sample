from copy import deepcopy

from django.db import transaction

from app.errors import DraftConflictError, DraftNotEditableError
from app.models import ApplicationDraft, DraftUpload


@transaction.atomic
def update_attachments(
    *,
    draft_id,
    owner,
    expected_revision: int,
    attachments: list[dict],
) -> ApplicationDraft:
    draft = (
        ApplicationDraft.objects.for_update()
        .owned_by(owner)
        .select_related("application")
        .get(pk=draft_id)
    )
    if draft.status != ApplicationDraft.Status.EDITING:
        raise DraftNotEditableError(draft_id=draft_id)
    if draft.revision != expected_revision:
        raise DraftConflictError(
            expected_revision=expected_revision,
            current_revision=draft.revision,
        )

    previous = {item["row_id"]: item for item in draft.data.get("attachments", [])}
    normalized: list[dict] = []
    retained_row_ids = set()
    for item in attachments:
        if item.get("DELETE"):
            continue
        row_id = item["row_id"]
        row_id_text = str(row_id)
        retained_row_ids.add(row_id)
        old = previous.get(row_id_text, {})
        uploaded_file = item.get("file")
        if uploaded_file:
            old_upload = DraftUpload.objects.filter(draft=draft, row_id=row_id).first()
            if old_upload:
                old_storage, old_name = old_upload.file.storage, old_upload.file.name
                old_upload.delete()
                transaction.on_commit(
                    lambda storage=old_storage, name=old_name: storage.delete(name)
                )
            upload = DraftUpload.objects.create(
                draft=draft,
                row_id=row_id,
                file=uploaded_file,
                original_name=uploaded_file.name,
            )
            file_name = upload.original_name
            storage_name = upload.file.name
            upload_id = str(upload.id)
        else:
            file_name = old.get("file_name", item.get("existing_file_name", ""))
            storage_name = old.get("storage_name", "")
            upload_id = old.get("draft_upload_id")
        normalized.append(
            {
                "row_id": row_id_text,
                "source_id": str(item["source_id"]) if item.get("source_id") else None,
                "label": item["label"],
                "file_name": file_name,
                "storage_name": storage_name,
                "draft_upload_id": upload_id,
            }
        )

    removed_uploads = DraftUpload.objects.filter(draft=draft).exclude(row_id__in=retained_row_ids)
    removed_files = [(upload.file.storage, upload.file.name) for upload in removed_uploads]
    removed_uploads.delete()
    for storage, name in removed_files:
        transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))

    new_data = deepcopy(draft.data)
    new_data["attachments"] = normalized
    draft.data = new_data
    draft.revision += 1
    draft.save(update_fields=("data", "revision", "updated_at"))
    return draft
