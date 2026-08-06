from django.db import models


class ApplicationQuerySet(models.QuerySet):
    def owned_by(self, user):
        """所有者で絞り込む。"""
        return self.filter(owner=user)

    def with_details(self):
        """一覧・詳細・編集開始で必要な関連をまとめて読む。"""
        return self.select_related("owner", "reviewed_by").prefetch_related(
            "members",
            "attachments",
            "budget_items",
        )

    def with_history(self):
        """状態履歴を含めて読む。"""
        return self.prefetch_related("status_history__changed_by")

    def editable(self):
        """所有者編集が可能な状態のみ。"""
        return self.filter(status=self.model.Status.SUBMITTED)

    def for_review(self):
        """審査キュー用: 未着手または審査中。"""
        return self.filter(
            status__in=[
                self.model.Status.SUBMITTED,
                self.model.Status.UNDER_REVIEW,
            ]
        )

    def with_status(self, status: str):
        """ステータスで絞り込む。"""
        return self.filter(status=status)

    def matching_title(self, query: str):
        """申請名の部分一致。"""
        return self.filter(title__icontains=query)


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
