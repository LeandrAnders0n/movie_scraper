# Tamil Movie Ranking Dashboard

This project is a web scraping and data processing assignment designed to gather information on Tamil movies from Letterboxd, store them in a database, and rank them based on user review content and ratings. The project includes a web interface where users can view and filter movies by ranking and release date.

## Table of Contents
- [Assignment Overview](#assignment-overview)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Functionality](#functionality)
- [Usage](#usage)

---

## Assignment Overview
The task involves:
1. Scraping Tamil movies data from Letterboxd.
2. Storing movie metadata, including reviews, ratings, and release dates.
3. Ranking the movies, primarily based on the sentiment of user reviews and user ratings.
4. Displaying the rankings and metadata on a web dashboard.

## Project Structure
- **views.py**: Contains the main functions to scrape, rank, and display movies.
- **models.py**: Defines the `Movie` model in Django, which stores movie details.
- **templates/home.html**: HTML template for the dashboard interface.
- **README.md**: Documentation file.
- **static/css** and **static/js**: Contains CSS and JavaScript files for styling and client-side functionality.

## Setup Instructions

### Prerequisites
- Python 3.x
- Django
- Selenium
- ChromeDriver
- TextBlob for sentiment analysis
- scikit-learn for data normalization
- SQLite3 (default for Django)

### Installation
1. **Clone the repository**:
   ```bash
   git clone git@github.com:LeandrAnders0n/movie_scraper.git
   cd movie_scraper
   ```

2. **Install dependencies**:
   - Install required libraries:
     ```bash
     pip install django selenium webdriver-manager textblob scikit-learn lxml
     ```

3. **Run migrations**:
   Set up the database and apply migrations.
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Download the NLTK corpus for TextBlob**:
   TextBlob requires NLTK data for sentiment analysis:
   ```bash
   python -m textblob.download_corpora
   ```

### Setting Up ChromeDriver
Make sure ChromeDriver is compatible with your Chrome version:
```bash
webdriver-manager install
```

## Functionality

### 1. **Scraping Movie Data**
   - The `scrape_letterboxd_tamil_movies()` function in `views.py` scrapes movie data from Letterboxd, including title, release year, reviews, and user ratings.
   - Movie details are stored in the SQLite3 database using the `Movie` model.

### 2. **Calculating Rankings**
   - The `perform_movie_ranking()` function calculates a ranking score based on the sentiment of user reviews and user ratings.
   - Rankings are calculated using a weighted average: sentiment (80%) and user rating (20%).

### 3. **Displaying Rankings on Dashboard**
   - Movies are displayed in a responsive HTML dashboard, allowing users to filter movies by release date.

## Usage

### Scrape Movies and Calculate Rankings
1. **Start the Django Shell**:
   Run the following command in the terminal:
   ```bash
   python manage.py shell
   ```

2. **Run the Scraping Function**:
   Import and run the scraping function:
   ```python
   from movie_app.views import scrape_letterboxd_tamil_movies
   scrape_letterboxd_tamil_movies()
   ```

3. **Run the Ranking Function**:
   After scraping, run the ranking function to calculate rankings based on review sentiment and user ratings:
   ```python
   from movie_app.views import perform_movie_ranking
   perform_movie_ranking()
   ```

4. **Run the Server**:
   Start the Django development server to view the dashboard:
   ```bash
   python manage.py runserver
   ```

5. **Access the Dashboard**:
   Open the browser and go to `http://127.0.0.1:8000/dashboard/` to view the movie rankings dashboard.

### Filter Movies by Release Date
   - Use the date fields and filter buttons on the dashboard to display movies within a specific release date range.
