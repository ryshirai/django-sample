import uuid

import pytest

from app.drafts import CURRENT_SCHEMA_VERSION, BudgetItemPayload, ContactPayload, migrate_draft_data
from app.errors import ValidationError
from app.models import Application
from app.rules import ValidationCode
from app.services import create_draft, submit_draft, update_budget_items, update_contact
from app.tests.factories import complete_data, create_application

pytestmark = pytest.mark.django_db


def test_update_contact_replaces_section(user):
    draft = create_draft(owner=user)

    draft = update_contact(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
        payload=ContactPayload(
            phone="06-1111-2222",
            email="new@example.com",
            preferred_method="email",
            note="午前中のみ",
        ),
    )

    assert draft.data["contact"] == {
        "phone": "06-1111-2222",
        "email": "new@example.com",
        "preferred_method": "email",
        "note": "午前中のみ",
    }
    assert draft.revision == 2


def test_update_budget_items_replaces_rows(user):
    draft = create_draft(owner=user)
    row_id = uuid.uuid4()

    draft = update_budget_items(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
        budget_items=[
            BudgetItemPayload(
                row_id=row_id,
                source_id=None,
                description="旅費",
                amount=12000,
                category="travel",
            )
        ],
    )

    assert draft.data["budget_items"] == [
        {
            "row_id": str(row_id),
            "source_id": None,
            "description": "旅費",
            "amount": 12000,
            "category": "travel",
        }
    ]


def test_submit_persists_contact_and_budget_items(user):
    draft = create_draft(owner=user)
    draft.data = complete_data()
    draft.save(update_fields=("data",))

    application = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    assert application.contact_phone == "03-9876-5432"
    assert application.contact_email == "applicant@example.com"
    assert application.preferred_contact_method == Application.PreferredContactMethod.PHONE
    assert application.contact_note == "平日午後希望"
    budget_item = application.budget_items.get()
    assert budget_item.description == "会場使用料"
    assert budget_item.amount == 50000
    assert budget_item.category == "other"


def test_submit_edit_preserves_budget_source_id(user):
    application = create_application(owner=user)
    original_budget_id = application.budget_items.get().id
    draft = create_draft(owner=user, application_id=application.id)
    draft.data["budget_items"][0]["description"] = "機材費（更新）"
    draft.data["budget_items"][0]["amount"] = 15000
    draft.save(update_fields=("data",))

    result = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    assert result.budget_items.get().id == original_budget_id
    assert result.budget_items.get().description == "機材費（更新）"
    assert result.budget_items.get().amount == 15000


def test_validate_draft_requires_contact_phone(user):
    draft = create_draft(owner=user)
    draft.data = complete_data()
    draft.data["contact"]["phone"] = ""
    draft.save(update_fields=("data",))

    with pytest.raises(ValidationError) as raised:
        submit_draft(
            draft_id=draft.id,
            owner=user,
            expected_revision=draft.revision,
        )

    assert raised.value.errors["contact.phone"] == [ValidationCode.CONTACT_PHONE_REQUIRED]


def test_migrate_v1_draft_data_adds_contact_and_budget():
    v1_data = {
        "basic": {"title": "旧", "purpose": "目的"},
        "address": {
            "postal_code": "100-0001",
            "prefecture": "東京都",
            "city": "千代田区",
            "address_line": "1-1",
        },
        "members": [],
        "attachments": [],
    }

    migrated = migrate_draft_data(v1_data, from_version=1)

    assert migrated["contact"] == {
        "phone": "",
        "email": "",
        "preferred_method": "",
        "note": "",
    }
    assert migrated["budget_items"] == []
    assert CURRENT_SCHEMA_VERSION == 2


def test_ensure_current_schema_persists_v1_draft(user):
    """読取経路で v1 Draft が CURRENT まで進み永続化される。"""
    from app.models import ApplicationDraft
    from app.services import ensure_current_schema

    draft = ApplicationDraft.objects.create(
        owner=user,
        data={
            "basic": {"title": "旧", "purpose": "目的"},
            "address": {
                "postal_code": "100-0001",
                "prefecture": "東京都",
                "city": "千代田区",
                "address_line": "1-1",
            },
            "members": [],
            "attachments": [],
        },
        schema_version=1,
    )

    updated = ensure_current_schema(draft=draft)
    draft.refresh_from_db()

    assert updated.schema_version == CURRENT_SCHEMA_VERSION
    assert draft.schema_version == CURRENT_SCHEMA_VERSION
    assert "contact" in draft.data
    assert draft.data["budget_items"] == []
