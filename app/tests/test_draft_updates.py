import uuid

import pytest

from app.drafts import BasicPayload, MemberPayload
from app.errors import DraftConflictError
from app.services import create_draft, update_basic, update_members

pytestmark = pytest.mark.django_db


def test_update_draft_increments_revision(user):
    draft = create_draft(owner=user)

    updated = update_basic(
        draft_id=draft.id,
        owner=user,
        expected_revision=1,
        payload=BasicPayload(title="変更後", purpose="変更後の目的"),
    )

    assert updated.revision == 2
    assert updated.data["basic"] == {"title": "変更後", "purpose": "変更後の目的"}


def test_dynamic_rows_keep_uuid_identity(user):
    draft = create_draft(owner=user)
    row_id = uuid.uuid4()

    updated = update_members(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
        members=[
            MemberPayload(
                row_id=row_id,
                source_id=None,
                name="担当者",
                email="member@example.com",
                role="owner",
            )
        ],
    )

    assert updated.data["members"][0]["row_id"] == str(row_id)


def test_stale_revision_raises_conflict_and_does_not_overwrite(user):
    draft = create_draft(owner=user)
    update_basic(
        draft_id=draft.id,
        owner=user,
        expected_revision=1,
        payload=BasicPayload(title="先勝ち", purpose="最初の更新"),
    )

    with pytest.raises(DraftConflictError) as raised:
        update_basic(
            draft_id=draft.id,
            owner=user,
            expected_revision=1,
            payload=BasicPayload(title="後勝ちにしてはいけない", purpose="競合更新"),
        )

    draft.refresh_from_db()
    assert raised.value.params["current_revision"] == 2
    assert draft.data["basic"]["title"] == "先勝ち"
