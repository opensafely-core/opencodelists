"""Initial migration for shared usage models."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CodeUsageRelease",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "coding_system",
                    models.CharField(
                        choices=[
                            ("snomedct", "SNOMED CT"),
                            ("icd10", "ICD-10"),
                            ("opcs4", "OPCS-4"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "period",
                    models.CharField(
                        help_text="Period identifier, e.g. '2023-24' or '2023'",
                        max_length=20,
                    ),
                ),
                ("source_url", models.URLField(max_length=500)),
                ("imported_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "unique_together": {("coding_system", "period")},
            },
        ),
        migrations.CreateModel(
            name="CodeUsageEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="The code/ID from the coding system (e.g. SNOMED CT concept ID)",
                        max_length=18,
                    ),
                ),
                ("usage", models.IntegerField(blank=True, null=True)),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="coding_systems_usage.codeusagerelease",
                    ),
                ),
            ],
            options={
                "unique_together": {("release", "code")},
            },
        ),
        migrations.AddIndex(
            model_name="codeusagerelease",
            index=models.Index(
                fields=["coding_system", "period"],
                name="coding_syst_coding__f96c46_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="codeusageentry",
            index=models.Index(
                fields=["code"],
                name="coding_syst_code_4fe896_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="codeusageentry",
            index=models.Index(fields=["release"], name="coding_syst_release_76d1c3_idx"),
        ),
    ]
