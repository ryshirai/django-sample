from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from app.models import Application

from .draft_cleanup import discard_editing_drafts_for_application
from .status_history import record_status_change


@transaction.atomic
def cancel_application(
    *,
    application_id: UUID,
    owner: AbstractBaseUser,
) -> Application:
    """所有者自身の申請済み申請を取り消す。"""
    application = (
        Application.objects.select_for_update().owned_by(owner).get(pk=application_id)
    )
    previous_status = application.status
    now = timezone.now()
    application.cancel(cancelled_at=now)
    application.save(update_fields=("status", "cancelled_at", "updated_at"))
    discard_editing_drafts_for_application(application=application)
    record_status_change(
        application=application,
        from_status=previous_status,
        to_status=application.status,
        changed_by=owner,
    )
    return application
