# Generated by Django 5.1 on 2024-11-30 01:55

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0002_userwrappedhistory_delete_wrappedreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='userwrappedhistory',
            name='generated_on',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userwrappedhistory',
            name='timeframe',
            field=models.CharField(choices=[('short_term', 'Short Term'), ('medium_term', 'Medium Term'), ('long_term', 'Long Term')], max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='userwrappedhistory',
            unique_together={('user_id', 'timeframe')},
        ),
    ]
