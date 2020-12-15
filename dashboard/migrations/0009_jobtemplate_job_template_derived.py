# Generated by Django 2.0.8 on 2020-11-19 13:18

from django.conf import settings
from django.db import migrations, models


def add_push_trans_template(apps, schema_editor):

    if not settings.MIGRATE_INITIAL_DATA:
        return

    JobTemplate = apps.get_model('dashboard', 'JobTemplate')

    job_templates = [
        JobTemplate(job_template_type="pushtrans", job_template_name="Push Translations",
                    job_template_desc="Clone package source repository, "
                                      "filter translations and upload to the CI platform.",
                    job_template_params="{package_name,repo_type,repo_branch,pipeline_uuid,target_langs}",
                    job_template_json_str='{"job":{"ci_pipeline":"%PIPELINE_UUID%","exception":"raise",'
                                          '"execution":"sequential","name":"push translations",'
                                          '"package":"%PACKAGE_NAME%","return_type":"json",'
                                          '"tasks":[{"clone":[{"name":"git repo"},{"type":"%REPO_TYPE%"},'
                                          '{"branch":"%REPO_BRANCH%"},{"recursive":false}]},'
                                          '{"filter":[{"name":"files"},{"ext":"PO"}]},{"upload":[{"name":"Push files"},'
                                          '{"target_langs":"%TARGET_LANGS%"},{"prehook":"skip"},{"posthook":"skip"},'
                                          '{"update":false}]}],"type":"pushtrans"}}'
                    ),
    ]

    JobTemplate.objects.bulk_create(job_templates)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_auto_20201028_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='job_template_derived',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(add_push_trans_template, reverse_code=migrations.RunPython.noop),
    ]
