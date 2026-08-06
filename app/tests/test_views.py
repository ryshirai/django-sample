import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from app.drafts import empty_draft_data
from app.messages import ERROR_MESSAGES
from app.models import ApplicationDraft
from app.tests.factories import complete_data

pytestmark = pytest.mark.django_db


def test_basic_post_uses_post_redirect_get(client, user):
    client.force_login(user)
    draft = ApplicationDraft.objects.create(owner=user, data=empty_draft_data())

    response = client.post(
        reverse("app:draft-basic", args=(draft.id,)),
        {"revision": 1, "title": "画面更新", "purpose": "PRG確認", "next": "address"},
    )

    assert response.status_code == 302
    assert response.url == reverse("app:draft-address", args=(draft.id,))
    draft.refresh_from_db()
    assert draft.data["basic"]["title"] == "画面更新"


def test_submitted_draft_redirects_with_domain_error_not_404(client, user):
    """所有者の確定済み Draft は 404 ではなく DomainError 文言で一覧へ戻る。"""
    client.force_login(user)
    draft = ApplicationDraft.objects.create(
        owner=user,
        data=complete_data(),
        status=ApplicationDraft.Status.SUBMITTED,
    )

    response = client.get(reverse("app:draft-basic", args=(draft.id,)))

    assert response.status_code == 302
    assert response.url == reverse("app:application-list")
    message_texts = [str(item) for item in get_messages(response.wsgi_request)]
    assert ERROR_MESSAGES["draft_not_editable"] in message_texts
