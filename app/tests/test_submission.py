import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from app.drafts import AttachmentPayload
from app.errors import ValidationError
from app.models import Application, ApplicationDraft
from app.rules import ValidationCode
from app.services import create_draft, submit_draft, update_attachments
from app.tests.factories import complete_data, create_application

pytestmark = pytest.mark.django_db


def test_submit_draft_creates_formal_models_atomically(user):
    draft = create_draft(owner=user)
    draft.data = complete_data()
    draft.save(update_fields=("data",))

    application = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    draft.refresh_from_db()
    assert application.title == "新規申請"
    assert application.status == Application.Status.SUBMITTED
    assert application.members.get().email == "taro@example.com"
    assert draft.application == application
    assert draft.status == ApplicationDraft.Status.SUBMITTED
    assert draft.revision == 2


def test_submit_edit_draft_updates_application_and_preserves_member_source(user):
    application = create_application(owner=user)
    original_member_id = application.members.get().id
    draft = create_draft(owner=user, application_id=application.id)
    draft.data["basic"]["title"] = "編集済み申請"
    draft.data["members"][0]["name"] = "更新担当者"
    draft.save(update_fields=("data",))

    result = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    assert result.id == application.id
    assert result.title == "編集済み申請"
    assert result.members.get().id == original_member_id
    assert result.members.get().name == "更新担当者"


def test_whole_draft_validation_raises_domain_error_and_rolls_back(user):
    draft = create_draft(owner=user)
    original_revision = draft.revision

    with pytest.raises(ValidationError) as raised:
        submit_draft(
            draft_id=draft.id,
            owner=user,
            expected_revision=original_revision,
        )

    draft.refresh_from_db()
    assert raised.value.errors["basic.title"] == [ValidationCode.BASIC_TITLE_REQUIRED]
    assert draft.status == ApplicationDraft.Status.EDITING
    assert draft.revision == original_revision
    assert Application.objects.count() == 0


def test_staged_attachment_is_referenced_by_formal_model(user):
    draft = create_draft(owner=user)
    draft.data = complete_data()
    draft.save(update_fields=("data",))
    row_id = uuid.uuid4()
    draft = update_attachments(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
        attachments=[
            AttachmentPayload(
                row_id=row_id,
                source_id=None,
                label="本人確認書類",
                file=SimpleUploadedFile("identity.txt", b"sample"),
                existing_file_name="",
                delete=False,
            )
        ],
    )

    application = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    attachment = application.attachments.get()
    assert attachment.original_name == "identity.txt"
    assert attachment.file.name.startswith("application-files/")
