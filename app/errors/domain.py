from dataclasses import dataclass, field
from typing import Any


@dataclass(eq=False)
class DomainError(Exception):
    code: str
    params: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.code


class ValidationError(DomainError):
    def __init__(self, *, errors: dict[str, list[str]]) -> None:
        super().__init__(code="draft_validation_error", params={"errors": errors})
        self.errors = errors


class DraftConflictError(DomainError):
    def __init__(self, *, expected_revision: int, current_revision: int | None) -> None:
        super().__init__(
            code="draft_conflict",
            params={
                "expected_revision": expected_revision,
                "current_revision": current_revision,
            },
        )


class ApplicationLockedError(DomainError):
    def __init__(self, *, application_id) -> None:
        super().__init__(
            code="application_locked",
            params={"application_id": str(application_id)},
        )


class DraftNotEditableError(DomainError):
    def __init__(self, *, draft_id) -> None:
        super().__init__(code="draft_not_editable", params={"draft_id": str(draft_id)})


class InvalidApplicationStateError(DomainError):
    def __init__(self, *, application_id, current_status: str, operation: str) -> None:
        super().__init__(
            code="invalid_application_state",
            params={
                "application_id": str(application_id),
                "current_status": current_status,
                "operation": operation,
            },
        )


class StaffPermissionError(DomainError):
    def __init__(self) -> None:
        super().__init__(code="staff_permission_required")
