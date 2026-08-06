import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from app.errors import DraftNotEditableError

from .application import Application
from .querysets import ApplicationDraftQuerySet


class ApplicationDraft(models.Model):
    class Status(models.TextChoices):
        EDITING = "editing", "編集中"
        SUBMITTED = "submitted", "確定済み"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application_drafts",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.PROTECT,
        related_name="drafts",
        null=True,
        blank=True,
    )
    data = models.JSONField(default=dict)
    revision = models.PositiveBigIntegerField(default=1)
    # 新規作成の既定。読取時は services.ensure_current_schema が CURRENT まで進める。
    schema_version = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status, default=Status.EDITING)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ApplicationDraftQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(revision__gte=1),
                name="application_draft_revision_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(schema_version__gte=1),
                name="application_draft_schema_version_gte_1",
            ),
            # 値は Status と揃える（Meta から外側の Status は参照できない）。
            models.CheckConstraint(
                condition=Q(status__in=["editing", "submitted"]),
                name="application_draft_valid_status",
            ),
            models.UniqueConstraint(
                fields=("owner", "application"),
                condition=Q(status="editing", application__isnull=False),
                name="one_editing_draft_per_application_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pk} rev.{self.revision}"

    def ensure_editable(self) -> None:
        """編集中でなければ DraftNotEditableError。"""
        if self.status != self.Status.EDITING:
            raise DraftNotEditableError(draft_id=self.pk)


def draft_upload_path(instance, filename: str) -> str:
    # Draft と正式添付が同じストレージキーを共有する。
    return f"application-files/{instance.id}/{filename}"


class DraftUpload(models.Model):
    """編集中の一時添付。確定後は行だけ消し、ファイルオブジェクトは正式側が参照する。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(
        ApplicationDraft,
        on_delete=models.CASCADE,
        related_name="uploads",
    )
    row_id = models.UUIDField()
    file = models.FileField(upload_to=draft_upload_path, max_length=500)
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("draft", "row_id"),
                name="draft_upload_unique_row",
            ),
        ]

    def __str__(self) -> str:
        return self.original_name
