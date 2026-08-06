from django.db import models


class ApplicationQuerySet(models.QuerySet):
    def visible_to(self, user):
        return self.filter(owner=user)

    def with_details(self):
        return self.select_related("owner").prefetch_related("members", "attachments")

    def editable(self):
        return self.exclude(status=self.model.Status.LOCKED)


class ApplicationDraftQuerySet(models.QuerySet):
    def owned_by(self, user):
        return self.filter(owner=user)

    def editing(self):
        return self.filter(status=self.model.Status.EDITING)

    def for_update(self):
        return self.select_for_update()
