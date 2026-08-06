import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from app.errors import ApplicationLockedError, InvalidApplicationStateError

from .querysets import ApplicationQuerySet


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "申請済み"
        UNDER_REVIEW = "under_review", "審査中"
        APPROVED = "approved", "承認済み"
        REJECTED = "rejected", "却下"
        CANCELLED = "cancelled", "取消済み"
        LOCKED = "locked", "ロック済み"

    class PreferredContactMethod(models.TextChoices):
        PHONE = "phone", "電話"
        EMAIL = "email", "メール"
        EITHER = "either", "どちらでも"

    # 所有者による再編集が許される状態。
    EDITABLE_STATUSES = frozenset({Status.SUBMITTED})

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    title = models.CharField(max_length=200)
    purpose = models.TextField()
    postal_code = models.CharField(max_length=8)
    prefecture = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address_line = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=PreferredContactMethod.choices,
    )
    contact_note = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.SUBMITTED)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_applications",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ApplicationQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            # 値は Status と揃える（Meta から外側の Status は参照できない）。
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "submitted",
                        "under_review",
                        "approved",
                        "rejected",
                        "cancelled",
                        "locked",
                    ]
                ),
                name="application_valid_status",
            ),
            models.CheckConstraint(
                condition=Q(preferred_contact_method__in=["phone", "email", "either"]),
                name="application_valid_preferred_contact_method",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def ensure_editable(self) -> None:
        """所有者編集が不可なら DomainError。"""
        if self.status == self.Status.LOCKED:
            raise ApplicationLockedError(application_id=self.pk)
        if self.status not in self.EDITABLE_STATUSES:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="edit",
            )

    def submit(self, *, submitted_at) -> None:
        # 新規作成時は pk がまだ無いので ensure_editable を飛ばす。
        if self.pk:
            self.ensure_editable()
        self.status = self.Status.SUBMITTED
        self.submitted_at = submitted_at
        self.rejection_reason = ""
        self.reviewed_by = None
        self.reviewed_at = None
        self.cancelled_at = None

    def start_review(self) -> None:
        if self.status != self.Status.SUBMITTED:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="start_review",
            )
        self.status = self.Status.UNDER_REVIEW

    def approve(self, *, reviewer, reviewed_at) -> None:
        if self.status != self.Status.UNDER_REVIEW:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="approve",
            )
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = reviewed_at
        self.rejection_reason = ""

    def reject(self, *, reviewer, reviewed_at, reason: str) -> None:
        if self.status != self.Status.UNDER_REVIEW:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="reject",
            )
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = reviewed_at
        self.rejection_reason = reason

    def cancel(self, *, cancelled_at) -> None:
        if self.status != self.Status.SUBMITTED:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="cancel",
            )
        self.status = self.Status.CANCELLED
        self.cancelled_at = cancelled_at

    def lock(self) -> None:
        if self.status not in {self.Status.SUBMITTED, self.Status.APPROVED}:
            raise InvalidApplicationStateError(
                application_id=self.pk,
                current_status=self.status,
                operation="lock",
            )
        self.status = self.Status.LOCKED


class ApplicationMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "責任者"
        CONTACT = "contact", "連絡担当"
        MEMBER = "member", "担当者"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="members",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ("position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("application", "email"),
                name="application_member_unique_email",
            ),
            models.UniqueConstraint(
                fields=("application", "position"),
                name="application_member_unique_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


def application_attachment_path(instance, filename: str) -> str:
    # 通常の確定フローは storage_name を直接代入する。直書き時のフォールバック先。
    return f"application-files/{instance.id}/{filename}"


class ApplicationAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    label = models.CharField(max_length=100)
    file = models.FileField(upload_to=application_attachment_path, max_length=500)
    original_name = models.CharField(max_length=255)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ("position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("application", "position"),
                name="application_attachment_unique_position",
            ),
        ]

    def __str__(self) -> str:
        return self.label


class ApplicationBudgetItem(models.Model):
    class Category(models.TextChoices):
        EQUIPMENT = "equipment", "設備"
        TRAVEL = "travel", "旅費"
        PERSONNEL = "personnel", "人件費"
        OTHER = "other", "その他"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="budget_items",
    )
    description = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=Category.choices)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ("position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("application", "position"),
                name="application_budget_item_unique_position",
            ),
            models.CheckConstraint(
                condition=Q(category__in=["equipment", "travel", "personnel", "other"]),
                name="application_budget_item_valid_category",
            ),
            models.CheckConstraint(
                condition=Q(amount__gte=1),
                name="application_budget_item_amount_gte_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.description} ({self.amount})"


class ApplicationStatusHistory(models.Model):
    """申請ステータス遷移の監査ログ。表示文言は持たない。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="application_status_changes",
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "application status histories"

    def __str__(self) -> str:
        return f"{self.from_status or '-'} -> {self.to_status}"
