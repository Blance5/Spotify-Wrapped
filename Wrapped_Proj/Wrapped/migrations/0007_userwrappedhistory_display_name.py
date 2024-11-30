# Generated by Django 5.1 on 2024-11-30 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0006_wrapcounter_alter_userwrappedhistory_wrap_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userwrappedhistory',
            name='display_name',
            field=models.CharField(blank=True, help_text='A user-friendly name for the wrap.', max_length=255, null=True),
        ),
    ]