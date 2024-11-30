# Generated by Django 5.1 on 2024-11-30 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0003_userwrappedhistory_generated_on_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userwrappedhistory',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='userwrappedhistory',
            name='wrap_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='userwrappedhistory',
            unique_together={('user_id', 'timeframe', 'wrap_id')},
        ),
    ]
