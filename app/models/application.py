import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from app.errors import ApplicationLockedError, InvalidApplicationStateError

from .querysets import ApplicationQuerySet


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "申請済み"
        LOCKED = "locked", "ロック済み"

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
    status = models.CharField(max_length=20, choices=Status, default=Status.SUBMITTED)
    submitted_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ApplicationQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["submitted", "locked"]),
                name="application_valid_status",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def ensure_editable(self) -> None:
        if self.status == self.Status.LOCKED:
            raise ApplicationLockedError(application_id=self.pk)

    def submit(self, *, submitted_at) -> None:
        self.ensure_editable()
        self.status = self.Status.SUBMITTED
        self.submitted_at = submitted_at

    def lock(self) -> None:
        if self.status != self.Status.SUBMITTED:
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
    return f"applications/{instance.application_id}/{instance.id}/{filename}"


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
