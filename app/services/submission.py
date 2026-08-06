from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from app.drafts import command_from_draft, validate_draft
from app.errors import DraftConflictError, DraftNotEditableError, ValidationError
from app.messages import VALIDATION_MESSAGES
from app.models import (
    Application,
    ApplicationAttachment,
    ApplicationDraft,
    ApplicationMember,
)


@transaction.atomic
def submit_draft(*, draft_id, owner, expected_revision: int) -> Application:
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

    validate_draft(draft.data)
    command = command_from_draft(draft)
    now = timezone.now()

    if draft.application_id:
        application = (
            Application.objects.select_for_update().visible_to(owner).get(pk=draft.application_id)
        )
        application.ensure_editable()
    else:
        application = Application(owner=owner, submitted_at=now)

    application.title = command.title
    application.purpose = command.purpose
    application.postal_code = command.postal_code
    application.prefecture = command.prefecture
    application.city = command.city
    application.address_line = command.address_line
    application.submit(submitted_at=now)
    _full_clean_or_domain_error(application)
    application.save()

    _save_members(application=application, commands=command.members)
    _save_attachments(application=application, commands=command.attachments)

    draft.application = application
    draft.status = ApplicationDraft.Status.SUBMITTED
    draft.submitted_at = now
    draft.revision += 1
    draft.save(update_fields=("application", "status", "submitted_at", "revision", "updated_at"))
    draft.uploads.all().delete()
    return application


def _save_members(*, application: Application, commands) -> None:
    existing = {member.id: member for member in application.members.select_for_update()}
    claimed_ids = {item.source_id for item in commands if item.source_id}
    if not claimed_ids.issubset(existing):
        raise ValidationError(errors={"members": [VALIDATION_MESSAGES["invalid_member_source"]]})

    application.members.exclude(id__in=claimed_ids).delete()
    kept = [existing[item.source_id] for item in commands if item.source_id]
    for position, member in enumerate(kept):
        member.email = f"temporary-{member.id}@invalid.local"
        member.position = 100_000 + position
        member.save(update_fields=("email", "position"))

    for position, item in enumerate(commands):
        member = existing.get(item.source_id) or ApplicationMember(application=application)
        member.name = item.name
        member.email = item.email
        member.role = item.role
        member.position = position
        _full_clean_or_domain_error(member, prefix="members")
        member.save()


def _save_attachments(*, application: Application, commands) -> None:
    existing = {
        attachment.id: attachment for attachment in application.attachments.select_for_update()
    }
    claimed_ids = {item.source_id for item in commands if item.source_id}
    if not claimed_ids.issubset(existing):
        raise ValidationError(
            errors={"attachments": [VALIDATION_MESSAGES["invalid_attachment_source"]]}
        )

    removed = application.attachments.exclude(id__in=claimed_ids)
    removed_files = [(item.file.storage, item.file.name) for item in removed]
    removed.delete()
    for position, attachment in enumerate(existing.values()):
        if attachment.id in claimed_ids:
            attachment.position = 100_000 + position
            attachment.save(update_fields=("position",))

    retained_names = set()
    for position, item in enumerate(commands):
        attachment = existing.get(item.source_id) or ApplicationAttachment(application=application)
        old_name = attachment.file.name if attachment.pk else None
        attachment.label = item.label
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
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        errors = {
            f"{prefix}.{field}": [str(message) for message in messages]
            for field, messages in exc.message_dict.items()
        }
        raise ValidationError(errors=errors) from exc
