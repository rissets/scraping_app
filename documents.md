Project Brief: Nexus Aggregator

AI Persona: You are a highly skilled Lead Backend Developer specializing in Python, data engineering, and API architecture. You think systematically, write clean and efficient code, and always consider scalability and reliability. You take pride in your elegant and functional work.
Vision & Core Mission (The Vibe)

We are building "Nexus Aggregator," an intelligent and powerful information-gathering engine. Its purpose is not just to fetch data, but to transform the noise of the internet into a clear, structured signal. This application will become a reliable data source for analysts, journalists, and other developers who need fast, filtered access to the latest news and articles.

Your mission is to design and build the backbone of this system: a fast, secure, and versatile REST API using Python.
Core Architecture & Technology

    Language: Python 3.9+

    API Framework: FastAPI. We're choosing it for its speed, automatic data validation, and excellent interactive documentation (Swagger UI).

    Scraping Libraries:

        requests for making HTTP requests.

        BeautifulSoup4 and lxml for parsing HTML.

        Also, consider Newspaper3k for more intelligent article extraction where needed.

    Authentication: API Key. Simple yet effective for controlling access.

Key Functionality (Mission Objectives)

You must build two primary endpoints with the following functionality:

1. News & Article Search Endpoint (/api/v1/search)

This is the heart of the Nexus Aggregator. This endpoint must be highly flexible.

    HTTP Method: GET

    Authentication: Required via an API Key in the header (e.g., X-API-KEY).

    Input Parameters (Query Params):

        query (string, required): The topic or keyword to search for.

        sources (string, optional): Desired news sources, comma-separated (e.g., google_news,bing_news). If empty, search all supported sources.

        category (string, optional): News category (e.g., technology, business, sports).

        format (string, optional, default: json): Desired output format. Options: json, csv, xml.

    Processing Logic:

        Validate the API Key.

        Retrieve the input parameters.

        Dynamically call the appropriate scraper functions based on the sources parameter.

        Aggregate and normalize the results from various sources into a single, standard data structure. Each news/article item must have the following fields: title, link, source_name, snippet (a brief description), published_date (if available), and scraped_timestamp.

        Based on the format parameter, return the response in the requested format (direct JSON response, a CSV file, or an XML file).

    Response Structure (JSON Example):

    {
      "query": "AI in Indonesia",
      "item_count": 2,
      "results": [
        {
          "title": "The Growth of AI in Indonesia is Accelerating",
          "link": "https://news.example.com/ai-indonesia",
          "source_name": "Google News",
          "snippet": "New government regulations are encouraging the adoption of artificial intelligence across various industrial sectors...",
          "published_date": "2024-07-29T10:00:00Z",
          "scraped_timestamp": "2024-07-29T12:34:56Z"
        },
        {
          "title": "Bing Highlights Local AI Startups",
          "link": "https://bing.example.news/startup-ai",
          "source_name": "Bing News",
          "snippet": "In its latest report, Bing News highlights three promising AI startups from Indonesia...",
          "published_date": "2024-07-28T18:30:00Z",
          "scraped_timestamp": "2024-07-29T12:34:57Z"
        }
      ]
    }

2. Specific URL Scraper Endpoint (/api/v1/scrape-url)

This endpoint serves as a utility tool for fetching content from a single target URL.

    HTTP Method: POST

    Authentication: Required via an API Key in the header.

    Input Body (JSON):

    {
      "url": "https://www.example.com/path/to/article",
      "output_mode": "response"
    }

        url (string, required): The full URL of the article to be scraped.

        output_mode (string, optional, default: response): Options: response (return in the API response) or markdown_file (save as a file on the server).

    Processing Logic:

        Validate the API Key and the input URL.

        Use requests and BeautifulSoup4 (or Newspaper3k) to fetch and clean the main content of the article (title, main text, author, publication date).

        Convert the cleaned content into Markdown format.

        If output_mode is response, return the Markdown in a JSON response.

        If output_mode is markdown_file, save the content as a .md file on the server and return a success status or the file path.

    Response Structure (if output_mode: 'response'):

    {
      "source_url": "https://www.example.com/path/to/article",
      "status": "success",
      "markdown_content": "# Article Title\n\n**Author:** John Doe\n**Date:** 2024-07-29\n\nThis is the first paragraph of the article. And this is the second paragraph..."
    }

Implementation Guidelines & Best Practices

    Modularity: Separate the logic. Create distinct files for main.py (API endpoints), scraper.py (scraping functions), auth.py (API key management), and utils.py (format converters).

    Error Handling: The application must be robust. Handle potential errors like a target website being down, changes in HTML structure, invalid URLs, or connection timeouts. Return informative error messages.

    Configuration: Do not hardcode values. Store valid API keys or other configurations in a .env file and use a library like python-dotenv to read them.

    Documentation: Fully leverage FastAPI's automatic documentation features. Use Pydantic models to define input and output schemas so the API documentation is clear and interactive.

    Dependencies: Provide a complete requirements.txt file to make the project easy to set up in any environment.

First Step: Start by creating the project structure and its basic files. Then, build the scraper function for one source first (e.g., Google News) as a proof of concept. After that, build the first API endpoint to use it. Let's get started!