from django.contrib import admin

from app.models import (
    Application,
    ApplicationAttachment,
    ApplicationBudgetItem,
    ApplicationDraft,
    ApplicationMember,
    ApplicationStatusHistory,
)


class ApplicationMemberInline(admin.TabularInline):
    model = ApplicationMember
    extra = 0


class ApplicationAttachmentInline(admin.TabularInline):
    model = ApplicationAttachment
    extra = 0


class ApplicationBudgetItemInline(admin.TabularInline):
    model = ApplicationBudgetItem
    extra = 0


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "comment", "created_at")
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "submitted_at", "updated_at")
    list_filter = ("status", "preferred_contact_method")
    search_fields = ("title", "owner__username", "contact_email")
    inlines = (
        ApplicationMemberInline,
        ApplicationBudgetItemInline,
        ApplicationAttachmentInline,
        ApplicationStatusHistoryInline,
    )


@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "application", "status", "revision", "updated_at")
    list_filter = ("status", "schema_version")
    readonly_fields = ("data", "revision", "schema_version")


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("application", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)
    search_fields = ("application__title", "changed_by__username")
