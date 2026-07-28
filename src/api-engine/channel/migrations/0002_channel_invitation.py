import common.utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChannelInvitation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=common.utils.make_uuid,
                        help_text="Channel Invitation ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("SIGNING", "Signing"),
                            ("READY", "Ready"),
                            ("ACCEPTED", "Accepted"),
                            ("REJECTED", "Rejected"),
                            ("FAILED", "Failed"),
                            ("CANCELED", "Canceled"),
                        ],
                        default="DRAFT",
                        help_text="Channel invitation status",
                        max_length=32,
                    ),
                ),
                (
                    "artifact",
                    models.FileField(
                        blank=True,
                        help_text="Update Artifact",
                        null=True,
                        upload_to="channel_invitations/",
                    ),
                ),
                (
                    "artifact_hash",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Artifact Hash",
                        max_length=64,
                    ),
                ),
                (
                    "required_signatures",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Required Signatures",
                    ),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Error Message",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "channel",
                    models.ForeignKey(
                        help_text="Invitation Channel",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="channel.channel",
                    ),
                ),
                (
                    "creator_organization",
                    models.ForeignKey(
                        help_text="Creator Organization",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_invitations",
                        to="organization.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="ChannelInvitationSignature",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=common.utils.make_uuid,
                        help_text="Channel Invitation Signature ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "artifact_hash",
                    models.CharField(
                        help_text="Artifact Hash",
                        max_length=64,
                    ),
                ),
                (
                    "signed_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "invitation",
                    models.ForeignKey(
                        help_text="Invitation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signatures",
                        to="channel.channelinvitation",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Signing Organization",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitation_signatures",
                        to="organization.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("signed_at",),
            },
        ),
        migrations.CreateModel(
            name="ChannelInvitationInvitee",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=common.utils.make_uuid,
                        help_text="Channel Invitation Invitee ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ACCEPTED", "Accepted"),
                            ("REJECTED", "Rejected"),
                        ],
                        default="PENDING",
                        help_text="Invitee Status",
                        max_length=32,
                    ),
                ),
                (
                    "responded_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "invitation",
                    models.ForeignKey(
                        help_text="Invitation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitees",
                        to="channel.channelinvitation",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Invited Organization",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitee_invitations",
                        to="organization.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
            },
        ),
        migrations.AddConstraint(
            model_name="channelinvitationsignature",
            constraint=models.UniqueConstraint(
                fields=("invitation", "organization"),
                name="unique_channel_invitation_signature",
            ),
        ),
        migrations.AddConstraint(
            model_name="channelinvitationinvitee",
            constraint=models.UniqueConstraint(
                fields=("invitation", "organization"),
                name="unique_channel_invitation_invitee",
            ),
        ),
    ]
