# Generated by Django 2.0.8 on 2019-07-12 11:46

import dashboard.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_auto_20190618_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='CacheBuildDetails',
            fields=[
                ('cache_build_details_id', models.AutoField(primary_key=True, serialize=False)),
                ('build_system', models.CharField(max_length=200, verbose_name='Build System')),
                ('build_tag', models.CharField(max_length=200, verbose_name='Build Tag')),
                ('build_details_json_str', models.TextField(blank=True, null=True)),
                ('job_log_json_str', models.TextField(blank=True, null=True)),
                ('package_name', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dashboard.Package', to_field='package_name', verbose_name='Package')),
            ],
            options={
                'db_table': 'ts_cachebuilddetails',
            },
            bases=(dashboard.models.ModelMixin, models.Model),
        ),
    ]
