from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=50)
    release_date = models.DateField()
    user_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    ranking = models.FloatField(default=0.0)  

    def __str__(self):
        return self.title

class Review(models.Model):
    movie = models.ForeignKey(Movie, related_name='reviews', on_delete=models.CASCADE)
    content = models.TextField()
    sentiment_score = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.movie.title}"
