from django.db import migrations, models


def set_default_icons(apps, schema_editor):
    EquipmentType = apps.get_model('equipment', 'EquipmentType')
    icon_map = {
        'Tablet': 'bi-tablet',
        'Projector': 'bi-projector',
        'Screen': 'bi-display',
        'Dongle': 'bi-usb-plug',
        'Power Extension': 'bi-plug',
    }
    for et in EquipmentType.objects.all():
        et.icon = icon_map.get(et.name, 'bi-box-seam')
        et.save()


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0006_equipmenttype_and_fk_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmenttype',
            name='icon',
            field=models.CharField(default='bi-box-seam', max_length=60),
        ),
        migrations.RunPython(set_default_icons, migrations.RunPython.noop),
    ]
