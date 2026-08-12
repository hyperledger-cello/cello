from django.db import migrations, models

import common.validators


def convert_blank_agent_urls_to_null(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    Organization.objects.filter(agent_url="").update(agent_url=None)


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0002_organization_msp_id"),
    ]

    operations = [
        migrations.RunPython(
            convert_blank_agent_urls_to_null,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="organization",
            name="agent_url",
            field=models.CharField(
                default=None,
                help_text="Organization Agent URL",
                max_length=2048,
                null=True,
                unique=True,
                validators=[common.validators.validate_url],
            ),
        ),
    ]
