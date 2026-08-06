from collections.abc import Callable
from copy import deepcopy
from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.utils import timezone

from app.errors import DraftConflictError, DraftNotEditableError
from app.models import ApplicationDraft


def update_draft_data(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    mutate: Callable[[dict], None],
) -> ApplicationDraft:
    """mutate で data を書き換え、revision 一致時だけ CAS 更新する。"""
    draft = ApplicationDraft.objects.owned_by(owner).get(pk=draft_id)
    draft.ensure_editable()

    new_data = deepcopy(draft.data)
    mutate(new_data)
    updated = (
        ApplicationDraft.objects.owned_by(owner)
        .editing()
        .filter(pk=draft_id, revision=expected_revision)
        .update(
            data=new_data,
            revision=expected_revision + 1,
            updated_at=timezone.now(),
        )
    )
    if updated != 1:
        current = (
            ApplicationDraft.objects.owned_by(owner)
            .filter(pk=draft_id)
            .values("revision", "status")
            .first()
        )
        if current is None or current["status"] != ApplicationDraft.Status.EDITING:
            raise DraftNotEditableError(draft_id=draft_id)
        raise DraftConflictError(
            expected_revision=expected_revision,
            current_revision=current["revision"],
        )
    draft.data = new_data
    draft.revision = expected_revision + 1
    return draft
