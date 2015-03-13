# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('album', models.CharField(max_length=255, verbose_name=b'Album name')),
                ('search', models.CharField(max_length=255, db_index=True)),
                ('sort', models.CharField(max_length=255, db_index=True)),
                ('label', models.CharField(max_length=200, null=True, db_index=True)),
                ('review', models.TextField(blank=True)),
                ('year', models.IntegerField(null=True, verbose_name=b'year first released', db_index=True)),
                ('location', models.CharField(max_length=25, db_index=True)),
                ('added_on', models.DateField(auto_now_add=True, verbose_name=b'date added to the library', null=True)),
            ],
            options={
                'ordering': ['sort'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('artist', models.CharField(unique=True, max_length=255, verbose_name=b'Artist name')),
                ('search', models.CharField(unique=True, max_length=255)),
                ('sort', models.CharField(max_length=255, db_index=True)),
                ('last_played', models.DateTimeField(null=True, verbose_name=b'last played at', blank=True)),
                ('times_played', models.IntegerField(default=0, verbose_name=b'number of times played')),
                ('info', models.TextField(blank=True)),
                ('url', models.URLField(blank=True)),
            ],
            options={
                'ordering': ['sort'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Concert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(db_index=True)),
                ('time', models.TimeField(db_index=True, null=True, blank=True)),
                ('we_present', models.BooleanField(default=False, verbose_name=b'Radio 1190 presents')),
                ('minimum_age', models.CharField(max_length=4, blank=True)),
                ('info', models.TextField(blank=True)),
                ('site', models.URLField(blank=True)),
            ],
            options={
                'ordering': ['date', 'time'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Performer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.SmallIntegerField()),
                ('performer', models.CharField(max_length=255)),
                ('artist', models.ForeignKey(blank=True, to='djpro.Artist', null=True)),
                ('concert', models.ForeignKey(to='djpro.Concert')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rotation', models.CharField(max_length=35)),
                ('max', models.SmallIntegerField(verbose_name=b'Suggested number')),
            ],
            options={
                'ordering': ['max'],
                'verbose_name': 'rotation level',
                'verbose_name_plural': 'rotation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('song', models.CharField(max_length=255, verbose_name=b'Song name')),
                ('search', models.CharField(max_length=255, null=True, db_index=True)),
                ('length', models.CharField(max_length=6, null=True, blank=True)),
                ('last_played', models.DateTimeField(null=True, verbose_name=b'last played at', blank=True)),
                ('times_played', models.IntegerField(default=0, verbose_name=b'number of times played')),
                ('track', models.CharField(max_length=5, null=True, blank=True)),
                ('track_num', models.IntegerField(db_index=True, null=True, blank=True)),
                ('tempo', models.CharField(max_length=5, null=True, blank=True)),
                ('ramp', models.CharField(max_length=5, null=True, blank=True)),
                ('post', models.CharField(max_length=5, null=True, blank=True)),
                ('rating', models.SmallIntegerField(default=1, choices=[(1, ''), (2, '\u2605'), (3, '\u2605\u2605'), (4, '\u2605\u2605\u2605'), (5, '\u2605\u2605\u2605\u2605'), (0, 'dirty'), (-2, 'DJ pick'), (-3, 'TuneTracker')])),
                ('added_on', models.DateField(auto_now_add=True, null=True)),
                ('album', models.ForeignKey(to='djpro.Album')),
                ('artist', models.ForeignKey(related_name='all_songs', to='djpro.Artist', null=True)),
                ('comp_artist', models.ForeignKey(related_name='comp_songs', blank=True, to='djpro.Artist', null=True)),
                ('rotation', models.ForeignKey(blank=True, to='djpro.Rotation', null=True)),
            ],
            options={
                'ordering': ['track_num', 'song'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('alias', models.CharField(max_length=75, null=True)),
                ('phone', models.CharField(max_length=15, null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('venue', models.CharField(unique=True, max_length=255)),
                ('sort', models.CharField(max_length=255, null=True, db_index=True)),
                ('location', models.CharField(max_length=255, blank=True)),
                ('default_minimum_age', models.CharField(max_length=4, blank=True)),
                ('default_time', models.TimeField(null=True, blank=True)),
                ('homepage', models.URLField(blank=True)),
            ],
            options={
                'ordering': ['venue'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='concert',
            name='artists',
            field=models.ManyToManyField(to='djpro.Artist', through='djpro.Performer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='concert',
            name='venue',
            field=models.ForeignKey(to='djpro.Venue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='album',
            name='artist',
            field=models.ForeignKey(blank=True, to='djpro.Artist', null=True),
            preserve_default=True,
        ),
    ]
