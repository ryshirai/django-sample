from django.db import models


class ApplicationQuerySet(models.QuerySet):
    def owned_by(self, user):
        """所有者で絞り込む。"""
        return self.filter(owner=user)

    def with_details(self):
        """一覧・編集開始で必要な関連をまとめて読む。"""
        return self.select_related("owner").prefetch_related("members", "attachments")

    def editable(self):
        """ロック済みを除く。"""
        return self.exclude(status=self.model.Status.LOCKED)


class ApplicationDraftQuerySet(models.QuerySet):
    def owned_by(self, user):
        """所有者で絞り込む。"""
        return self.filter(owner=user)

    def editing(self):
        """編集中 Draft のみ。"""
        return self.filter(status=self.model.Status.EDITING)

    def for_update(self):
        """行ロック付き読取。"""
        return self.select_for_update()
