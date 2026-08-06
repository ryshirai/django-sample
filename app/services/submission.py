from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from app.drafts import command_from_draft, validate_draft
from app.errors import DraftConflictError, ValidationError
from app.models import (
    Application,
    ApplicationAttachment,
    ApplicationBudgetItem,
    ApplicationDraft,
    ApplicationMember,
)
from app.rules import ValidationCode, validation_code_from_django

from .draft_schema import ensure_current_schema
from .status_history import record_status_change

# 一意制約を一時回避するための position 退避先。
TEMPORARY_POSITION_BASE = 100_000


@transaction.atomic
def submit_draft(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
) -> Application:
    """Draft を全体検証し、正式 Application へ原子的に反映する。"""
    draft = (
        ApplicationDraft.objects.for_update()
        .owned_by(owner)
        .select_related("application")
        .get(pk=draft_id)
    )
    draft.ensure_editable()
    draft = ensure_current_schema(draft=draft)
    if draft.revision != expected_revision:
        raise DraftConflictError(
            expected_revision=expected_revision,
            current_revision=draft.revision,
        )

    validate_draft(draft.data)
    command = command_from_draft(draft)
    now = timezone.now()
    previous_status = ""

    if draft.application_id:
        application = (
            Application.objects.select_for_update().owned_by(owner).get(pk=draft.application_id)
        )
        application.ensure_editable()
        previous_status = application.status
    else:
        application = Application(owner=owner, submitted_at=now)

    application.title = command.title
    application.purpose = command.purpose
    application.postal_code = command.postal_code
    application.prefecture = command.prefecture
    application.city = command.city
    application.address_line = command.address_line
    application.contact_phone = command.contact_phone
    application.contact_email = command.contact_email
    application.preferred_contact_method = command.preferred_contact_method
    application.contact_note = command.contact_note
    application.submit(submitted_at=now)
    _full_clean_or_domain_error(application)
    application.save()

    _save_members(application=application, commands=command.members)
    _save_budget_items(application=application, commands=command.budget_items)
    _save_attachments(application=application, commands=command.attachments)

    draft.application = application
    draft.status = ApplicationDraft.Status.SUBMITTED
    draft.submitted_at = now
    draft.revision += 1
    draft.save(update_fields=("application", "status", "submitted_at", "revision", "updated_at"))
    draft.uploads.all().delete()

    record_status_change(
        application=application,
        from_status=previous_status,
        to_status=application.status,
        changed_by=owner,
    )
    return application


def _save_members(*, application: Application, commands) -> None:
    existing = {member.id: member for member in application.members.select_for_update()}
    claimed_ids = {item.source_id for item in commands if item.source_id}
    if not claimed_ids.issubset(existing):
        raise ValidationError(errors={"members": [ValidationCode.INVALID_MEMBER_SOURCE]})

    application.members.exclude(id__in=claimed_ids).delete()
    kept = [existing[item.source_id] for item in commands if item.source_id]
    for position, member in enumerate(kept):
        member.email = f"temporary-{member.id}@invalid.local"
        member.position = TEMPORARY_POSITION_BASE + position
        member.save(update_fields=("email", "position"))

    for position, item in enumerate(commands):
        member = existing.get(item.source_id) or ApplicationMember(application=application)
        member.name = item.name
        member.email = item.email
        member.role = item.role
        member.position = position
        _full_clean_or_domain_error(member, prefix="members")
        member.save()


def _save_budget_items(*, application: Application, commands) -> None:
    existing = {item.id: item for item in application.budget_items.select_for_update()}
    claimed_ids = {item.source_id for item in commands if item.source_id}
    if not claimed_ids.issubset(existing):
        raise ValidationError(errors={"budget_items": [ValidationCode.INVALID_BUDGET_SOURCE]})

    application.budget_items.exclude(id__in=claimed_ids).delete()
    for position, budget_item in enumerate(existing.values()):
        if budget_item.id in claimed_ids:
            budget_item.position = TEMPORARY_POSITION_BASE + position
            budget_item.save(update_fields=("position",))

    for position, item in enumerate(commands):
        budget_item = existing.get(item.source_id) or ApplicationBudgetItem(
            application=application
        )
        budget_item.description = item.description
        budget_item.amount = item.amount
        budget_item.category = item.category
        budget_item.position = position
        _full_clean_or_domain_error(budget_item, prefix="budget_items")
        budget_item.save()


def _save_attachments(*, application: Application, commands) -> None:
    existing = {
        attachment.id: attachment for attachment in application.attachments.select_for_update()
    }
    claimed_ids = {item.source_id for item in commands if item.source_id}
    if not claimed_ids.issubset(existing):
        raise ValidationError(
            errors={"attachments": [ValidationCode.INVALID_ATTACHMENT_SOURCE]}
        )

    removed = application.attachments.exclude(id__in=claimed_ids)
    removed_files = [(item.file.storage, item.file.name) for item in removed]
    removed.delete()
    for position, attachment in enumerate(existing.values()):
        if attachment.id in claimed_ids:
            attachment.position = TEMPORARY_POSITION_BASE + position
            attachment.save(update_fields=("position",))

    retained_names = set()
    for position, item in enumerate(commands):
        attachment = existing.get(item.source_id) or ApplicationAttachment(application=application)
        old_name = attachment.file.name if attachment.pk else None
        attachment.label = item.label
        # Draft と同じストレージキーを正式行へ引き継ぐ。
        attachment.file.name = item.storage_name
        attachment.original_name = item.file_name
        attachment.position = position
        _full_clean_or_domain_error(attachment, prefix="attachments")
        attachment.save()
        retained_names.add(item.storage_name)
        if old_name and old_name != item.storage_name:
            removed_files.append((attachment.file.storage, old_name))

    for storage, name in removed_files:
        if name not in retained_names:
            transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))


def _full_clean_or_domain_error(instance, *, prefix: str = "application") -> None:
    """full_clean の失敗を言語非依存 ValidationCode へ変換して再送出する。"""
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        raise ValidationError(errors=_codes_from_django_validation(exc, prefix=prefix)) from exc


def _codes_from_django_validation(
    exc: DjangoValidationError,
    *,
    prefix: str,
) -> dict[str, list[str]]:
    """Django ValidationError を field -> [ValidationCode, ...] に変換する。"""
    if hasattr(exc, "error_dict"):
        return {
            f"{prefix}.{field}": [
                validation_code_from_django(error.code) for error in field_errors
            ]
            for field, field_errors in exc.error_dict.items()
        }
    return {
        prefix: [validation_code_from_django(error.code) for error in exc.error_list],
    }
