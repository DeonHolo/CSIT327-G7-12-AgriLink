from django.db import migrations


def add_other_category(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.get_or_create(
        name='Others',
        defaults={'description': 'Miscellaneous agricultural products'}
    )


def remove_other_category(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(name='Others').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_remove_savedcalculation_quantity_and_more'),
    ]

    operations = [
        migrations.RunPython(add_other_category, remove_other_category),
    ]
