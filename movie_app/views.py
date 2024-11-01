from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from lxml import html
from movie_app.models import Movie, Review
from django.db import IntegrityError
import time
from datetime import datetime
from textblob import TextBlob
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from django.shortcuts import render
from django.utils import timezone
import time

def scrape_letterboxd_tamil_movies():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=chrome_options)
    
    base_url = 'https://letterboxd.com/films/language/tamil/page/'

    page = 1  
    while True:
        url = f"{base_url}{page}/"
        browser.get(url)
        time.sleep(3)

        innerHTML = browser.execute_script("return document.body.innerHTML")
        tree = html.fromstring(innerHTML)

        titles = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-name')
        release_years = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-release-year')
        review_links = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-link')
        
        if not titles:
            break

        for title, year, review_link in zip(titles, release_years, review_links):
            full_review_link = f'https://letterboxd.com{review_link}'

            try:
                release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
                movie_instance, created = Movie.objects.get_or_create(
                    title=title,
                    genre='Tamil',
                    release_date=release_date
                )
                if created:
                    print(f"Created new movie entry: {title}")
                else:
                    print(f"Movie {title} already exists, updating reviews.")

                # Scrape and save each review and user rating
                average_user_rating = scrape_review_content_and_rating(browser, full_review_link, movie_instance)
                movie_instance.user_rating = average_user_rating
                movie_instance.save(update_fields=['user_rating'])
                print(f"Saved {title} with an average rating of {average_user_rating}")

            except IntegrityError:
                print(f"Failed to save {title}: Integrity error.")
            except ValueError as e:
                print(f"Failed to save {title}: {e}")

        page += 1  
    browser.quit()
    print("Scraping completed.")

# Scraping Functions
def scrape_review_content_and_rating(browser, review_link, movie_instance):
    browser.get(review_link)
    time.sleep(3)  # Allow page to load
    all_reviews = []
    all_ratings = []

    while True:
        innerHTML = browser.execute_script("return document.body.innerHTML")
        tree = html.fromstring(innerHTML)

        # Extract reviews from the Popular reviews section
        review_elements = tree.xpath('//ul[@class="film-popular-review"]/li[@class="film-detail"]/div[@class="film-detail-content"]/div[contains(@class, "body-text")]/div[@class="hidden-spoilers expanded-text"] | //ul[@class="film-popular-review"]/li[@class="film-detail"]/div[@class="film-detail-content"]/div[contains(@class, "body-text")]/p')
        
        for review_element in review_elements:
            review_text = review_element.text_content().strip()
            all_reviews.append(review_text)

            # Calculate sentiment score
            blob = TextBlob(review_text)
            sentiment_score = blob.sentiment.polarity

            # Save each review with its sentiment score
            Review.objects.create(
                movie=movie_instance,
                content=review_text,
                sentiment_score=sentiment_score,
                created_at=timezone.now()
            )

        # Extract user ratings from the Popular reviews section
        user_ratings = tree.xpath('//ul[@class="film-popular-review"]/li[@class="film-detail"]//span[contains(@class, "rating -green")]/text()')
        for rating in user_ratings:
            rating = rating.strip()
            if "★" in rating:
                all_ratings.append(len(rating) * 2)
            elif "½" in rating:
                all_ratings.append(1.5)
            else:
                try:
                    all_ratings.append(float(rating))
                except ValueError:
                    print("Unexpected rating format encountered:", rating)

        # Check for 'next' button to load more reviews
        next_button = tree.xpath('//a[contains(@class, "next")]/@href')
        if next_button:
            next_page_url = "https://letterboxd.com" + next_button[0]
            browser.get(next_page_url)
            time.sleep(2)
        else:
            break

    # Calculate average user rating for the movie
    average_user_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None
    return average_user_rating

from sklearn.preprocessing import MinMaxScaler
import numpy as np

def perform_movie_ranking():
    # Fetch all movies from the database
    movies = Movie.objects.all()

    # Initialize lists for scaling sentiment scores and user ratings
    average_sentiment_scores = []
    user_ratings = []

    # First pass: Calculate average sentiment scores for each movie
    for movie in movies:
        reviews = movie.reviews.all()
        if reviews.exists():
            # Calculate the average sentiment score from all reviews
            average_sentiment_score = sum(review.sentiment_score for review in reviews) / reviews.count()
        else:
            average_sentiment_score = 0.0  # Default if no reviews are available

        # Collect sentiment scores and user ratings for normalization
        average_sentiment_scores.append(average_sentiment_score)
        user_ratings.append(float(movie.user_rating or 0))

    # Normalize sentiment and user rating scores to 0–1 range
    scaler = MinMaxScaler()
    normalized_sentiment_scores = scaler.fit_transform(np.array(average_sentiment_scores).reshape(-1, 1)).flatten()
    normalized_user_ratings = scaler.fit_transform(np.array(user_ratings).reshape(-1, 1)).flatten()

    # Second pass: Assign ranking based on weighted sum and round to 3 decimal places
    for i, movie in enumerate(movies):
        # Calculate the ranking using normalized sentiment and user rating
        ranking = (
            normalized_sentiment_scores[i] * 0.8 +  
            normalized_user_ratings[i] * 0.2         
        )
        movie.ranking = round(ranking, 3)  # Round to 3 decimal places
        movie.save(update_fields=['ranking'])

    print("Ranking update complete.")




def home(request):
    movies = Movie.objects.all().order_by('-ranking')
    print(movies)
    movie_data = [{
        'title': movie.title,
        'release_date': movie.release_date,
        'user_rating': movie.user_rating,
        'ranking': movie.ranking
    } for movie in movies]
    return render(request, 'home.html', {'movie_data': movie_data})

