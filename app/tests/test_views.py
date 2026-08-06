import pytest
from django.urls import reverse

from app.drafts import empty_draft_data
from app.models import ApplicationDraft

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
