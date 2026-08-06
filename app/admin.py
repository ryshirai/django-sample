from django.contrib import admin

from app.models import Application, ApplicationAttachment, ApplicationDraft, ApplicationMember


class ApplicationMemberInline(admin.TabularInline):
    model = ApplicationMember
    extra = 0


class ApplicationAttachmentInline(admin.TabularInline):
    model = ApplicationAttachment
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "submitted_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "owner__username")
    inlines = (ApplicationMemberInline, ApplicationAttachmentInline)


@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "application", "status", "revision", "updated_at")
    list_filter = ("status", "schema_version")
    readonly_fields = ("data", "revision", "schema_version")
