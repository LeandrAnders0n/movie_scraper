# Generated by Django 4.2.2 on 2024-10-31 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movie_app', '0003_remove_movie_review_content_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='sentiment_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
