import uuid

from django.utils import timezone

from app.drafts import empty_draft_data
from app.models import Application, ApplicationBudgetItem, ApplicationMember


def create_application(*, owner, status=Application.Status.SUBMITTED) -> Application:
    application = Application.objects.create(
        owner=owner,
        title="既存申請",
        purpose="既存の目的",
        postal_code="100-0001",
        prefecture="東京都",
        city="千代田区",
        address_line="千代田1-1",
        contact_phone="03-1234-5678",
        contact_email="contact@example.com",
        preferred_contact_method=Application.PreferredContactMethod.EMAIL,
        contact_note="",
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
    ApplicationBudgetItem.objects.create(
        application=application,
        description="既存機材費",
        amount=10000,
        category=ApplicationBudgetItem.Category.EQUIPMENT,
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
    data["contact"] = {
        "phone": "03-9876-5432",
        "email": "applicant@example.com",
        "preferred_method": "phone",
        "note": "平日午後希望",
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
    data["budget_items"] = [
        {
            "row_id": str(uuid.uuid4()),
            "source_id": None,
            "description": "会場使用料",
            "amount": 50000,
            "category": "other",
        }
    ]
    return data
