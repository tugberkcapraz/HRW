from newspaper import Article
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_articles(start_date, end_date):
    # Construct the GDELT API URL with the specified date range
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query=%20(domain:.hrw.org%20OR%20domainis:hrw.org)&mode=ArtList&maxrecords=250&startdatetime={start_date}&enddatetime={end_date}&format=json"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching articles: {response.status_code}")
        return []  # Return an empty list on error

    # Log the raw response text for debugging
    print("Raw response text:", response.text)

    # Check if the response content is empty
    if not response.content:
        print("Error: Received empty response from the API.")
        return []  # Return an empty list on empty response

    try:
        articles_df = pd.json_normalize(response.json()["articles"])  # Use response.json() directly
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []  # Return an empty list on JSON parse error

    # Process each article to download and parse
    articles = []
    for index, item in articles_df.iterrows():
        article_url = item['url']
        article = Article(article_url)
        article.download()
        article.parse()
        articles.append({
            'title': article.title,
            'text': article.text,
            'url': article_url,
            'published_date': item['seendate']  # Assuming 'seendate' is available
        })
    
    return articles


def save_to_csv(articles, filename):
    df = pd.DataFrame(articles)
    df.to_csv(filename, index=False)


def main():
    start_date = "20240101000000"  # Start date in GDELT format (YYYYMMDDHHMMSS)
    end_date = "20240828000000"    # End date in GDELT format (YYYYMMDDHHMMSS)
    all_articles = []

    # Loop through each month until the end date
    current_start_date = datetime.strptime(start_date, "%Y%m%d%H%M%S")
    end_date_dt = datetime.strptime(end_date, "%Y%m%d%H%M%S")

    while current_start_date < end_date_dt:
        current_end_date = (current_start_date + timedelta(days=30)).strftime("%Y%m%d%H%M%S")
        
        # Ensure the end date does not exceed the specified end date
        if current_end_date > end_date:
            current_end_date = end_date

        articles = fetch_articles(current_start_date.strftime("%Y%m%d%H%M%S"), current_end_date)
        all_articles.extend(articles)

        # Move to the next month
        current_start_date += timedelta(days=30)

    save_to_csv(all_articles, 'hrw_articles.csv')


if __name__ == "__main__":
    main()
