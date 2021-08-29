# Generated by Django 3.2.5 on 2021-08-29 11:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("test_app", "0003_alter_testbroker_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="testbroker",
            options={
                "permissions": [
                    ("unique_permission", "Unique permission"),
                    ("not_unique_permission", "Not unique permission"),
                ]
            },
        ),
        migrations.AlterModelOptions(
            name="testowner",
            options={
                "permissions": [("not_unique_permission", "Not unique permission")]
            },
        ),
    ]