# Generated by Django 5.1 on 2024-11-30 02:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0004_alter_userwrappedhistory_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userwrappedhistory',
            name='user_id',
            field=models.CharField(max_length=255),
        ),
    ]