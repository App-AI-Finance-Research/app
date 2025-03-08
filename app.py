import os
from flask import Flask, render_template, request, jsonify
import cohere
import requests
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

# Set your Cohere API Key here
cohere_api_key = "your_cohere_api_key"
co = cohere.Client(cohere_api_key)

# News API Key (Get your API key from newsapi.org)
NEWS_API_KEY = "your_news_api_key"
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Function to fetch news articles for a given company
def fetch_news(company_name):
    today = datetime.now()
    two_weeks_ago = today - timedelta(weeks=2)

    query = company_name + " stock"
    params = {
        'q': query,
        'from': two_weeks_ago.strftime('%Y-%m-%d'),
        'to': today.strftime('%Y-%m-%d'),
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5  # Top 5 news articles
    }

    response = requests.get(NEWS_API_URL, params=params)
    news_data = response.json()

    if news_data["status"] == "ok":
        articles = news_data["articles"]
        news_list = []
        for article in articles:
            news_list.append({
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "publishedAt": article["publishedAt"],
                "source": article["source"]["name"]
            })
        return news_list
    return []

# Function to generate financial summary and sentiment analysis using Cohere API
def analyze_news(news_list):
    system_message = """
    You are an equity research analyst. You need to search news associated with input company name, create a financial summary of news in 200 words, which contains impact on financial metrics e.g. EBITDA, PAT, Revenue, Costs, etc. Also perform a sentiment analysis of the news and categorize it into - Positive, Neutral or Negative depending on its impact on financial metrics. 
    Please respond in a table format with the following columns: Date, News Source, News Title, News Summary, Sentiment.
    """

    result = []
    for news in news_list:
        prompt = f"Company: {news['title']} \n{news['description']}\n"
        
        response = co.generate(
            model="xlarge",
            prompt=system_message + prompt,
            max_tokens=400
        )
        
        summary = response.text.strip()
        
        # Sentiment analysis (we can refine this part, for now let's assume it's part of the summary)
        sentiment = "Positive" if "positive" in summary.lower() else "Negative" if "negative" in summary.lower() else "Neutral"
        
        # Parse the date and format the response
        result.append({
            "Date": news["publishedAt"],
            "News Source": news["source"],
            "News Title": news["title"],
            "News Summary": summary,
            "Sentiment": sentiment
        })
    
    return result

# Home route to display the HTML form
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle the search query and generate results
@app.route('/search', methods=['POST'])
def search():
    user_query = request.form['company']
    news_list = fetch_news(user_query)
    
    if news_list:
        summarized_news = analyze_news(news_list)
    else:
        summarized_news = []

    return render_template('index.html', query=user_query, result=summarized_news)

# Run the Flask app on port 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)
