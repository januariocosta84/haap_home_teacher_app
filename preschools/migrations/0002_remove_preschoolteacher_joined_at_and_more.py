from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preschools', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='preschoolteacher',
            name='assigned_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='preschoolteacher',
            name='is_primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='preschoolteacher',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='preschoolteacher',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
    ]