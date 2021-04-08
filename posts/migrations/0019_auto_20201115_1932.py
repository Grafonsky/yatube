# Generated by Django 2.2.6 on 2020-11-15 15:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0018_auto_20201114_0256'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='name of constraint',
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='posts.Group'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='user_author'),
        ),
    ]