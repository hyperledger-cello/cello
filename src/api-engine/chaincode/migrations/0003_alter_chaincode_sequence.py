# Generated manually for default sequence value

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chaincode', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chaincode',
            name='sequence',
            field=models.IntegerField(
                default=1,
                help_text='Chaincode Sequence',
                validators=[MinValueValidator(1)],
            ),
        ),
    ]
