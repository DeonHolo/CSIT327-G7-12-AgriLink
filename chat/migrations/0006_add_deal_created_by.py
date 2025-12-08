# Generated migration for adding created_by field to Deal model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0005_add_deal_expires_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='created_by',
            field=models.ForeignKey(
                help_text='User who created this offer',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_deals',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
