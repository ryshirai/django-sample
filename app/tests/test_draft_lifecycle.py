import pytest

from app.drafts import CURRENT_SCHEMA_VERSION
from app.errors import ApplicationLockedError
from app.models import Application, ApplicationDraft
from app.services import create_draft, delete_draft
from app.tests.factories import create_application

pytestmark = pytest.mark.django_db


def test_create_new_draft(user):
    draft = create_draft(owner=user)

    assert draft.owner == user
    assert draft.application is None
    assert draft.revision == 1
    assert draft.schema_version == CURRENT_SCHEMA_VERSION
    assert draft.status == ApplicationDraft.Status.EDITING
    assert draft.data["members"] == []


def test_create_edit_draft_snapshots_application_once(user):
    application = create_application(owner=user)

    draft = create_draft(owner=user, application_id=application.id)
    application.title = "正式側だけ変更"
    application.save(update_fields=("title",))
    draft.refresh_from_db()

    assert draft.data["basic"]["title"] == "既存申請"
    assert draft.data["members"][0]["source_id"] == str(application.members.get().id)
    assert draft.data["members"][0]["row_id"]


def test_create_draft_for_locked_application_raises_domain_error(user):
    application = create_application(owner=user, status=Application.Status.LOCKED)

    with pytest.raises(ApplicationLockedError):
        create_draft(owner=user, application_id=application.id)


def test_delete_draft(user):
    draft = create_draft(owner=user)

    delete_draft(draft_id=draft.id, owner=user)

    assert not ApplicationDraft.objects.filter(id=draft.id).exists()
