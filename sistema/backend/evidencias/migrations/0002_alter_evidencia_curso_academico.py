from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidencias", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evidencia",
            name="curso_academico",
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name="curso académico"),
        ),
    ]
