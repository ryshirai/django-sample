from django.urls import path

from app import views

app_name = "app"

urlpatterns = [
    path("", views.application_list, name="application-list"),
    path("drafts/new/", views.draft_create, name="draft-create"),
    path(
        "applications/<uuid:application_id>/",
        views.application_detail,
        name="application-detail",
    ),
    path(
        "applications/<uuid:application_id>/edit/",
        views.edit_start,
        name="edit-start",
    ),
    path(
        "applications/<uuid:application_id>/cancel/",
        views.application_cancel,
        name="application-cancel",
    ),
    path("drafts/<uuid:draft_id>/delete/", views.draft_delete, name="draft-delete"),
    path("drafts/<uuid:draft_id>/basic/", views.basic_edit, name="draft-basic"),
    path("drafts/<uuid:draft_id>/address/", views.address_edit, name="draft-address"),
    path("drafts/<uuid:draft_id>/contact/", views.contact_edit, name="draft-contact"),
    path("drafts/<uuid:draft_id>/members/", views.members_edit, name="draft-members"),
    path("drafts/<uuid:draft_id>/budget/", views.budget_edit, name="draft-budget"),
    path(
        "drafts/<uuid:draft_id>/attachments/",
        views.attachments_edit,
        name="draft-attachments",
    ),
    path("drafts/<uuid:draft_id>/confirm/", views.confirm, name="draft-confirm"),
    path("reviews/", views.review_list, name="review-list"),
    path("reviews/<uuid:application_id>/", views.review_detail, name="review-detail"),
    path(
        "reviews/<uuid:application_id>/start/",
        views.review_start,
        name="review-start",
    ),
]
