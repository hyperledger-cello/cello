# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0002_channel_invitation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channelinvitationinvitee",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("ACCEPTED", "Accepted"),
                    ("REJECTED", "Rejected"),
                ],
                db_index=True,
                default="PENDING",
                help_text="Invitee Status",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="channelinvitation",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("SIGNING", "Signing"),
                    ("READY", "Ready"),
                    ("ACCEPTED", "Accepted"),
                    ("REJECTED", "Rejected"),
                    ("FAILED", "Failed"),
                    ("CANCELED", "Canceled"),
                ],
                db_index=True,
                default="DRAFT",
                help_text="Channel invitation status",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="channelinvitation",
            name="required_signatures",
            field=models.PositiveSmallIntegerField(
                default=1, help_text="Required Signatures"
            ),
        ),
    ]