# Generated by Django 5.1 on 2024-11-30 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Wrapped', '0005_alter_userwrappedhistory_user_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='WrapCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_wrap_id', models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.AlterField(
            model_name='userwrappedhistory',
            name='wrap_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
