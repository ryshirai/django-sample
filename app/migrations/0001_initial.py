# Generated for Django 5.2.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import app.models.application
import app.models.draft


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("purpose", models.TextField()),
                ("postal_code", models.CharField(max_length=8)),
                ("prefecture", models.CharField(max_length=20)),
                ("city", models.CharField(max_length=100)),
                ("address_line", models.CharField(max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[("submitted", "申請済み"), ("locked", "ロック済み")],
                        default="submitted",
                        max_length=20,
                    ),
                ),
                ("submitted_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at",),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["submitted", "locked"])),
                        name="application_valid_status",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ApplicationAttachment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("label", models.CharField(max_length=100)),
                (
                    "file",
                    models.FileField(
                        max_length=500, upload_to=app.models.application.application_attachment_path
                    ),
                ),
                ("original_name", models.CharField(max_length=255)),
                ("position", models.PositiveIntegerField()),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="app.application",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "position"),
                        name="application_attachment_unique_position",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ApplicationDraft",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("data", models.JSONField(default=dict)),
                ("revision", models.PositiveBigIntegerField(default=1)),
                ("schema_version", models.PositiveIntegerField(default=1)),
                (
                    "status",
                    models.CharField(
                        choices=[("editing", "編集中"), ("submitted", "確定済み")],
                        default="editing",
                        max_length=20,
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="drafts",
                        to="app.application",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="application_drafts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at",),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("revision__gte", 1)),
                        name="application_draft_revision_gte_1",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("schema_version__gte", 1)),
                        name="application_draft_schema_version_gte_1",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["editing", "submitted"])),
                        name="application_draft_valid_status",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("application__isnull", False), ("status", "editing")),
                        fields=("owner", "application"),
                        name="one_editing_draft_per_application_owner",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ApplicationMember",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "責任者"),
                            ("contact", "連絡担当"),
                            ("member", "担当者"),
                        ],
                        max_length=20,
                    ),
                ),
                ("position", models.PositiveIntegerField()),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="app.application",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "email"), name="application_member_unique_email"
                    ),
                    models.UniqueConstraint(
                        fields=("application", "position"),
                        name="application_member_unique_position",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DraftUpload",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("row_id", models.UUIDField()),
                (
                    "file",
                    models.FileField(max_length=500, upload_to=app.models.draft.draft_upload_path),
                ),
                ("original_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "draft",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="uploads",
                        to="app.applicationdraft",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("draft", "row_id"), name="draft_upload_unique_row"
                    )
                ],
            },
        ),
    ]
