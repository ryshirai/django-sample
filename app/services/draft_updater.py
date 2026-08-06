from collections.abc import Callable
from copy import deepcopy

from django.utils import timezone

from app.errors import DraftConflictError, DraftNotEditableError
from app.models import ApplicationDraft


def update_draft_data(
    *,
    draft_id,
    owner,
    expected_revision: int,
    mutate: Callable[[dict], None],
) -> ApplicationDraft:
    """JSON全体をcompare-and-swapで更新し、lost updateを防ぐ。"""
    draft = ApplicationDraft.objects.owned_by(owner).get(pk=draft_id)
    if draft.status != ApplicationDraft.Status.EDITING:
        raise DraftNotEditableError(draft_id=draft_id)

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
        current_revision = (
            ApplicationDraft.objects.owned_by(owner)
            .filter(pk=draft_id)
            .values_list("revision", flat=True)
            .first()
        )
        raise DraftConflictError(
            expected_revision=expected_revision,
            current_revision=current_revision,
        )
    draft.data = new_data
    draft.revision = expected_revision + 1
    return draft
