from django.db import migrations, models
import django.db.models.deletion


# Initial types: (name, serial_number_required)
INITIAL_TYPES = [
    ('Tablet',          True),
    ('Projector',       True),
    ('Screen',          False),
    ('Dongle',          False),
    ('Power Extension', False),
]

# Map old varchar values → new type names
TYPE_MAP = {
    'tablet':          'Tablet',
    'projector':       'Projector',
    'screen':          'Screen',
    'dongle':          'Dongle',
    'power_extension': 'Power Extension',
}


def seed_types_and_migrate(apps, schema_editor):
    EquipmentType = apps.get_model('equipment', 'EquipmentType')
    Equipment     = apps.get_model('equipment', 'Equipment')

    # Create initial types
    type_objects = {}
    for name, required in INITIAL_TYPES:
        obj, _ = EquipmentType.objects.get_or_create(name=name, defaults={'serial_number_required': required})
        type_objects[name] = obj

    # Map existing equipment records
    for eq in Equipment.objects.all():
        old_val = eq.equipment_type_old or ''
        new_name = TYPE_MAP.get(old_val)
        if new_name and new_name in type_objects:
            eq.equipment_type_id = type_objects[new_name].id
            eq.save(update_fields=['equipment_type_id'])


def reverse_migrate(apps, schema_editor):
    Equipment = apps.get_model('equipment', 'Equipment')
    REVERSE_MAP = {v: k for k, v in TYPE_MAP.items()}
    for eq in Equipment.objects.select_related('equipment_type').all():
        if eq.equipment_type:
            eq.equipment_type_old = REVERSE_MAP.get(eq.equipment_type.name, 'tablet')
            eq.save(update_fields=['equipment_type_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0005_replace_adapter_with_dongle_power_extension'),
    ]

    operations = [
        # 1. Create the EquipmentType table
        migrations.CreateModel(
            name='EquipmentType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('serial_number_required', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'equipment_types',
                'ordering': ['name'],
            },
        ),

        # 2. Rename the old varchar column so we can populate the FK before removing it
        migrations.RenameField(
            model_name='equipment',
            old_name='equipment_type',
            new_name='equipment_type_old',
        ),

        # 3. Add the new nullable FK column
        migrations.AddField(
            model_name='equipment',
            name='equipment_type',
            field=models.ForeignKey(
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='equipment_items',
                to='equipment.equipmenttype',
            ),
        ),

        # 4. Data migration: seed types + populate FK from old varchar
        migrations.RunPython(seed_types_and_migrate, reverse_migrate),

        # 5. Make the FK non-nullable (all rows now have a value)
        migrations.AlterField(
            model_name='equipment',
            name='equipment_type',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='equipment_items',
                to='equipment.equipmenttype',
            ),
        ),

        # 6. Drop the old varchar column
        migrations.RemoveField(
            model_name='equipment',
            name='equipment_type_old',
        ),

        # 7. Make serial_number nullable (not required for all types)
        migrations.AlterField(
            model_name='equipment',
            name='serial_number',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
