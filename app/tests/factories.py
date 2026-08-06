import uuid

from django.utils import timezone

from app.drafts import empty_draft_data
from app.models import Application, ApplicationMember


def create_application(*, owner, status=Application.Status.SUBMITTED) -> Application:
    application = Application.objects.create(
        owner=owner,
        title="既存申請",
        purpose="既存の目的",
        postal_code="100-0001",
        prefecture="東京都",
        city="千代田区",
        address_line="千代田1-1",
        status=status,
        submitted_at=timezone.now(),
    )
    ApplicationMember.objects.create(
        application=application,
        name="既存担当者",
        email="existing@example.com",
        role=ApplicationMember.Role.OWNER,
        position=0,
    )
    return application


def complete_data() -> dict:
    """submit 可能な最小 Draft data。empty_draft_data を土台に上書きする。"""
    data = empty_draft_data()
    data["basic"] = {"title": "新規申請", "purpose": "設備を利用するため"}
    data["address"] = {
        "postal_code": "150-0001",
        "prefecture": "東京都",
        "city": "渋谷区",
        "address_line": "神宮前1-1",
    }
    data["members"] = [
        {
            "row_id": str(uuid.uuid4()),
            "source_id": None,
            "name": "山田太郎",
            "email": "taro@example.com",
            "role": "owner",
        }
    ]
    return data
