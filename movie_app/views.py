from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from lxml import html
from movie_app.models import Movie
from django.db import IntegrityError
import time
from datetime import datetime
from textblob import TextBlob
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from django.shortcuts import render


def scrape_letterboxd_tamil_movies():
    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--disable-software-rasterizer")  
    chrome_options.add_argument("--log-level=3")  

    # Initialize the Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=chrome_options)
    
    base_url = 'https://letterboxd.com/films/language/tamil/page/'

    # Start from the first page
    page = 1  
    while True:
        url = f"{base_url}{page}/"
        browser.get(url)
        # Allow time for the page to fully load
        time.sleep(3)  

        # Parse HTML content
        innerHTML = browser.execute_script("return document.body.innerHTML")
        tree = html.fromstring(innerHTML)

        # Extract data: titles, release years, and review links
        titles = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-name')
        release_years = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-release-year')
        review_links = tree.xpath('//ul[@class="poster-list -p70 -grid"]/li/div/@data-film-link')
        
        # If no more movies are found, break the loop
        if not titles:
            break

        # Loop through each scraped movie on this page
        for title, year, review_link in zip(titles, release_years, review_links):
            full_review_link = f'https://letterboxd.com{review_link}'
            review_content, user_rating = scrape_review_content_and_rating(browser, full_review_link)

            # Save to database
            try:
                # Default to Jan 1 if only year is provided
                release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")  
                Movie.objects.create(
                    title=title,
                    genre='Tamil',
                    release_date=release_date,
                    review_content=review_content,
                    user_rating=user_rating
                )
                print(f"Successfully saved {title} to the database.")
            except IntegrityError:
                print(f"Movie {title} already exists in the database.")
            except ValueError as e:
                print(f"Failed to save {title}: {e}")
        # Move to the next page
        page += 1  

    browser.quit()

def scrape_review_content_and_rating(browser, review_link):
    browser.get(review_link)
    # Wait for the page to load
    time.sleep(3)  

    # Initialize containers for aggregated review content and ratings
    all_reviews = []
    all_ratings = []

    # Loop to go through multiple review pages if they exist
    while True:
        innerHTML = browser.execute_script("return document.body.innerHTML")
        tree = html.fromstring(innerHTML)

        # Extract reviews from the Popular reviews section
        review_elements = tree.xpath('//ul[@class="film-popular-review"]/li[@class="film-detail"]/div[@class="film-detail-content"]/div[contains(@class, "body-text")]/div[@class="hidden-spoilers expanded-text"] | //ul[@class="film-popular-review"]/li[@class="film-detail"]/div[@class="film-detail-content"]/div[contains(@class, "body-text")]/p')
        
        # Extract each review and add to list
        for review_element in review_elements:
            review_text = review_element.text_content().strip()
            all_reviews.append(review_text)

        # Extract user ratings from the Popular reviews section
        user_ratings = tree.xpath('//ul[@class="film-popular-review"]/li[@class="film-detail"]//span[contains(@class, "rating -green")]/text()')
        for rating in user_ratings:
            rating = rating.strip()
            # Convert stars to numeric rating by counting symbols
            if "★" in rating:
                all_ratings.append(len(rating) * 2)  
            # Represent half-star ratings
            elif "½" in rating:
                all_ratings.append(1.5)  
            else:
                try:
                    # Convert to float if directly a numeric rating
                    all_ratings.append(float(rating))  
                except ValueError:
                    print("Unexpected rating format encountered:", rating)

        # Check if there’s a 'next' button to go to more review pages
        next_button = tree.xpath('//a[contains(@class, "next")]/@href')
        if next_button:
            next_page_url = "https://letterboxd.com" + next_button[0]
            browser.get(next_page_url)
            time.sleep(2)
        else:
            break  

    # Aggregate all review content and calculate the average rating
    combined_review_content = " ".join(all_reviews).strip()  
    average_user_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None

    return combined_review_content, average_user_rating

def perform_movie_ranking():
    # Fetch all movies from the database
    movies = Movie.objects.all()

    # Initialize arrays for scaling
    sentiment_scores = []
    user_ratings = []

    # First pass: Calculate sentiment scores and populate arrays
    for movie in movies:
        # Sentiment score based on review content
        blob = TextBlob(movie.review_content)
        # Range between -1 and 1
        sentiment_score = blob.sentiment.polarity 
        sentiment_scores.append(sentiment_score)

        # Add user ratings to the array for normalization
        user_ratings.append(float(movie.user_rating or 0))

    # Normalize sentiment and user rating scores to 0–1 range
    scaler = MinMaxScaler()
    normalized_sentiment_scores = scaler.fit_transform(np.array(sentiment_scores).reshape(-1, 1)).flatten()
    normalized_user_ratings = scaler.fit_transform(np.array(user_ratings).reshape(-1, 1)).flatten()

    # Second pass: Assign ranking based on weighted sum
    for i, movie in enumerate(movies):
        # Calculate the ranking using sentiment and user rating only
        ranking = (
            normalized_sentiment_scores[i] * 0.8 +  
            normalized_user_ratings[i] * 0.2         
        )
        movie.ranking = ranking
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

