from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preschools', '0005_alter_preschool_latitude_alter_preschool_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='preschool',
            name='emis_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='EMIS Code'),
        ),
    ]
