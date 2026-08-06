import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="application",
            name="contact_email",
            field=models.EmailField(default="legacy@example.invalid", max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="application",
            name="contact_note",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="application",
            name="contact_phone",
            field=models.CharField(default="000-0000-0000", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="application",
            name="preferred_contact_method",
            field=models.CharField(
                choices=[
                    ("phone", "電話"),
                    ("email", "メール"),
                    ("either", "どちらでも"),
                ],
                default="email",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="application",
            name="rejection_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="application",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="application",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reviewed_applications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="application",
            name="application_valid_status",
        ),
        migrations.AlterField(
            model_name="application",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "申請済み"),
                    ("under_review", "審査中"),
                    ("approved", "承認済み"),
                    ("rejected", "却下"),
                    ("cancelled", "取消済み"),
                    ("locked", "ロック済み"),
                ],
                default="submitted",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "status__in",
                        [
                            "submitted",
                            "under_review",
                            "approved",
                            "rejected",
                            "cancelled",
                            "locked",
                        ],
                    )
                ),
                name="application_valid_status",
            ),
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("preferred_contact_method__in", ["phone", "email", "either"])
                ),
                name="application_valid_preferred_contact_method",
            ),
        ),
        migrations.CreateModel(
            name="ApplicationBudgetItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("description", models.CharField(max_length=200)),
                ("amount", models.PositiveIntegerField()),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("equipment", "設備"),
                            ("travel", "旅費"),
                            ("personnel", "人件費"),
                            ("other", "その他"),
                        ],
                        max_length=20,
                    ),
                ),
                ("position", models.PositiveIntegerField()),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="budget_items",
                        to="app.application",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "position"),
                        name="application_budget_item_unique_position",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "category__in",
                                ["equipment", "travel", "personnel", "other"],
                            )
                        ),
                        name="application_budget_item_valid_category",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("amount__gte", 1)),
                        name="application_budget_item_amount_gte_1",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ApplicationStatusHistory",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("from_status", models.CharField(blank=True, max_length=20)),
                ("to_status", models.CharField(max_length=20)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="app.application",
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="application_status_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "application status histories",
                "ordering": ("-created_at",),
            },
        ),
    ]
