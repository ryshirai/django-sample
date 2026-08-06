from django.db import transaction

from app.models import Application, ApplicationDraft


def discard_editing_drafts_for_application(*, application: Application) -> None:
    """申請が編集不可になったとき、紐づく編集中 Draft と一時アップロードを捨てる。"""
    drafts = list(
        ApplicationDraft.objects.editing()
        .filter(application=application)
        .prefetch_related("uploads")
    )
    files: list[tuple] = []
    for draft in drafts:
        files.extend((upload.file.storage, upload.file.name) for upload in draft.uploads.all())
        draft.delete()
    for storage, name in files:
        transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
