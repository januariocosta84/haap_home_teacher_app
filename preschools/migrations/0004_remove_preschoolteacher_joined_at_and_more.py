from django.db import migrations


def drop_preschool_teacher_legacy_columns(apps, schema_editor):
    table_name = "preschool_teachers"
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }

    quoted_table = schema_editor.quote_name(table_name)
    for column_name in ("joined_at", "preschoolteacher"):
        if column_name in existing_columns:
            schema_editor.execute(
                f"ALTER TABLE {quoted_table} DROP COLUMN {schema_editor.quote_name(column_name)}"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('preschools', '0003_remove_preschoolteacher_joined_at_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    drop_preschool_teacher_legacy_columns,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='preschoolteacher',
                    name='joined_at',
                ),
                migrations.RemoveField(
                    model_name='preschoolteacher',
                    name='preschoolteacher',
                ),
            ],
        ),
    ]
