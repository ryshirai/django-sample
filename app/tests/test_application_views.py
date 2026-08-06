import pytest
from django.urls import reverse

from app.models import Application
from app.tests.factories import create_application

pytestmark = pytest.mark.django_db


def test_application_detail_shows_owner_application(client, user):
    application = create_application(owner=user)
    client.force_login(user)

    response = client.get(reverse("app:application-detail", args=(application.id,)))

    assert response.status_code == 200
    assert application.title.encode() in response.content


def test_application_detail_hides_other_users_application(client, user, django_user_model):
    other = django_user_model.objects.create_user(username="bob", password="password")
    application = create_application(owner=other)
    client.force_login(user)

    response = client.get(reverse("app:application-detail", args=(application.id,)))

    assert response.status_code == 404


def test_application_list_filters_by_status_and_query(client, user):
    create_application(owner=user)
    second = create_application(owner=user)
    second.title = "別件の設備申請"
    second.status = Application.Status.APPROVED
    second.save(update_fields=("title", "status"))
    client.force_login(user)

    response = client.get(
        reverse("app:application-list"),
        {"status": Application.Status.APPROVED, "query": "設備"},
    )

    assert response.status_code == 200
    titles = [item.title for item in response.context["applications"]]
    assert titles == ["別件の設備申請"]


def test_application_cancel_from_detail(client, user):
    application = create_application(owner=user)
    client.force_login(user)

    response = client.post(reverse("app:application-cancel", args=(application.id,)))

    assert response.status_code == 302
    application.refresh_from_db()
    assert application.status == Application.Status.CANCELLED
