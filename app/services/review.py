from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from app.errors import StaffPermissionError, ValidationError
from app.models import Application
from app.rules import ValidationCode

from .draft_cleanup import discard_editing_drafts_for_application
from .status_history import record_status_change


def _ensure_staff(*, reviewer: AbstractBaseUser) -> None:
    """審査 Service の権限最終防衛。View の staff チェックと dual にする。"""
    if not getattr(reviewer, "is_staff", False):
        raise StaffPermissionError()


@transaction.atomic
def start_review(
    *,
    application_id: UUID,
    reviewer: AbstractBaseUser,
) -> Application:
    """申請を審査中にする。"""
    _ensure_staff(reviewer=reviewer)
    application = Application.objects.select_for_update().get(pk=application_id)
    previous_status = application.status
    application.start_review()
    application.save(
        update_fields=("status", "updated_at"),
    )
    discard_editing_drafts_for_application(application=application)
    record_status_change(
        application=application,
        from_status=previous_status,
        to_status=application.status,
        changed_by=reviewer,
    )
    return application


@transaction.atomic
def approve_application(
    *,
    application_id: UUID,
    reviewer: AbstractBaseUser,
) -> Application:
    """審査中の申請を承認する。"""
    _ensure_staff(reviewer=reviewer)
    application = Application.objects.select_for_update().get(pk=application_id)
    previous_status = application.status
    now = timezone.now()
    application.approve(reviewer=reviewer, reviewed_at=now)
    application.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ),
    )
    record_status_change(
        application=application,
        from_status=previous_status,
        to_status=application.status,
        changed_by=reviewer,
    )
    return application


@transaction.atomic
def reject_application(
    *,
    application_id: UUID,
    reviewer: AbstractBaseUser,
    reason: str,
) -> Application:
    """審査中の申請を却下する。理由は必須。"""
    _ensure_staff(reviewer=reviewer)
    cleaned_reason = reason.strip()
    if not cleaned_reason:
        raise ValidationError(
            errors={"rejection_reason": [ValidationCode.REJECTION_REASON_REQUIRED]}
        )

    application = Application.objects.select_for_update().get(pk=application_id)
    previous_status = application.status
    now = timezone.now()
    application.reject(reviewer=reviewer, reviewed_at=now, reason=cleaned_reason)
    application.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ),
    )
    record_status_change(
        application=application,
        from_status=previous_status,
        to_status=application.status,
        changed_by=reviewer,
        comment=cleaned_reason,
    )
    return application
