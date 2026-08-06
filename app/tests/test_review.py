import pytest
from django.urls import reverse

from app.errors import InvalidApplicationStateError, StaffPermissionError, ValidationError
from app.models import Application, ApplicationDraft, ApplicationStatusHistory
from app.rules import ValidationCode
from app.services import (
    approve_application,
    cancel_application,
    create_draft,
    reject_application,
    start_review,
    submit_draft,
)
from app.tests.factories import complete_data, create_application

pytestmark = pytest.mark.django_db


def test_start_review_moves_submitted_to_under_review(user, staff_user):
    application = create_application(owner=user)

    result = start_review(application_id=application.id, reviewer=staff_user)

    assert result.status == Application.Status.UNDER_REVIEW
    history = ApplicationStatusHistory.objects.get(application=result)
    assert history.from_status == Application.Status.SUBMITTED
    assert history.to_status == Application.Status.UNDER_REVIEW
    assert history.changed_by == staff_user


def test_approve_application_records_reviewer(user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)

    result = approve_application(application_id=application.id, reviewer=staff_user)

    assert result.status == Application.Status.APPROVED
    assert result.reviewed_by == staff_user
    assert result.reviewed_at is not None
    assert ApplicationStatusHistory.objects.filter(
        application=result,
        to_status=Application.Status.APPROVED,
    ).exists()


def test_reject_application_requires_reason(user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)

    with pytest.raises(ValidationError) as raised:
        reject_application(
            application_id=application.id,
            reviewer=staff_user,
            reason="   ",
        )

    assert raised.value.errors["rejection_reason"] == [ValidationCode.REJECTION_REASON_REQUIRED]


def test_reject_application_stores_reason(user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)

    result = reject_application(
        application_id=application.id,
        reviewer=staff_user,
        reason="要件を満たしていない",
    )

    assert result.status == Application.Status.REJECTED
    assert result.rejection_reason == "要件を満たしていない"
    history = ApplicationStatusHistory.objects.filter(
        application=result,
        to_status=Application.Status.REJECTED,
    ).get()
    assert history.comment == "要件を満たしていない"


def test_cancel_application_only_when_submitted(user):
    application = create_application(owner=user)

    result = cancel_application(application_id=application.id, owner=user)

    assert result.status == Application.Status.CANCELLED
    assert result.cancelled_at is not None


def test_cancel_under_review_raises_invalid_state(user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)

    with pytest.raises(InvalidApplicationStateError):
        cancel_application(application_id=application.id, owner=user)


def test_under_review_is_not_editable(user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)
    application.refresh_from_db()

    with pytest.raises(InvalidApplicationStateError):
        application.ensure_editable()


def test_submit_records_initial_status_history(user):
    draft = create_draft(owner=user)
    draft.data = complete_data()
    draft.save(update_fields=("data",))

    application = submit_draft(
        draft_id=draft.id,
        owner=user,
        expected_revision=draft.revision,
    )

    history = ApplicationStatusHistory.objects.get(application=application)
    assert history.from_status == ""
    assert history.to_status == Application.Status.SUBMITTED
    assert history.changed_by == user


def test_review_list_requires_staff(client, user, staff_user):
    client.force_login(user)
    response = client.get(reverse("app:review-list"))
    assert response.status_code == 302

    client.force_login(staff_user)
    response = client.get(reverse("app:review-list"))
    assert response.status_code == 200


def test_review_detail_approve_flow(client, user, staff_user):
    application = create_application(owner=user)
    start_review(application_id=application.id, reviewer=staff_user)
    client.force_login(staff_user)

    response = client.post(
        reverse("app:review-detail", args=(application.id,)),
        {"action": "approve"},
    )

    assert response.status_code == 302
    application.refresh_from_db()
    assert application.status == Application.Status.APPROVED


def test_start_review_rejects_non_staff(user):
    application = create_application(owner=user)

    with pytest.raises(StaffPermissionError):
        start_review(application_id=application.id, reviewer=user)


def test_start_review_discards_editing_drafts(user, staff_user):
    application = create_application(owner=user)
    draft = create_draft(owner=user, application_id=application.id)
    assert draft.status == ApplicationDraft.Status.EDITING

    start_review(application_id=application.id, reviewer=staff_user)

    assert not ApplicationDraft.objects.filter(pk=draft.pk).exists()


def test_cancel_application_discards_editing_drafts(user):
    application = create_application(owner=user)
    draft = create_draft(owner=user, application_id=application.id)

    cancel_application(application_id=application.id, owner=user)

    assert not ApplicationDraft.objects.filter(pk=draft.pk).exists()
