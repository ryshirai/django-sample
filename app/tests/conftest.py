import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="alice", password="password")


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="reviewer",
        password="password",
        is_staff=True,
    )


@pytest.fixture(autouse=True)
def temporary_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
