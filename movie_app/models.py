from django.db import models

# In movie_app/models.py
class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=50)
    release_date = models.DateField()
    review_content = models.TextField()
    user_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    ranking = models.FloatField(default=0.0)  # Ensure this field is added

    def __str__(self):
        return self.title
