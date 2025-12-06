from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_add_other_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedcalculation',
            name='category',
            field=models.CharField(blank=True, help_text='Category selected during calculation', max_length=150),
        ),
    ]
