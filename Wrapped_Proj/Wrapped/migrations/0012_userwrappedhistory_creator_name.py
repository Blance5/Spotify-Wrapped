# Generated by Django 5.1.3 on 2024-12-01 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0011_userwrappedhistory_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='userwrappedhistory',
            name='creator_name',
            field=models.CharField(default='Unknown', max_length=255),
        ),
    ]