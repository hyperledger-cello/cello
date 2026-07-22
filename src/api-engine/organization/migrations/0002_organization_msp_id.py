from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="msp_id",
            field=models.CharField(
                blank=True,
                help_text="Fabric MSP ID",
                max_length=256,
                unique=True,
            ),
            preserve_default=False,
        ),
    ]
