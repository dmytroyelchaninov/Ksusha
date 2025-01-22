import scrapy
import json
from chronicle.parse_parameters import ARTICLES, MAX_PAGES_TO_LOAD, TEST_SCRAPED_URLS
from chronicle.utils import clean_data_and_run_tests

# Parses through the https://qa.brightspot.chronicle.com/article/ to find articles urls, 
# pushes 'load more' button MAX_PAGES_TO_LOAD times
# writes the urls to articles.json
class ArticleHunterSpider(scrapy.Spider):
    name = "article-hunter"
    allowed_domains = ["qa.brightspot.chronicle.com"]
    start_urls = ["https://qa.brightspot.chronicle.com/article/"]

    custom_settings = {
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.articles = {}
        self.pages_loaded = 0
        self.max_pages = MAX_PAGES_TO_LOAD

    def start_requests(self):
        self.logger.warning(f"{'='*50} STARTING SCRAPPING URLS {'='*50}")
        # launch default start_urls
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                self.parse,
            )

    def parse(self, response):
        article_cards = response.css("div.ListLoadMore-items div.ContentPromo-side")
        for card in article_cards:
            article_url = card.css("div.ContentPromo-side-title a::attr(href)").get()
            if article_url:
                article_url = response.urljoin(article_url)
                yield scrapy.Request(url=article_url, callback=self.parse_article)

        load_more = response.css("div.ListLoadMore-nextPage a::attr(href)").get()
        if load_more and self.pages_loaded < self.max_pages:
            self.pages_loaded += 1
            next_page = response.urljoin(load_more)
            self.logger.info(f"Loading page {self.pages_loaded}")
            yield scrapy.Request(url=next_page, callback=self.parse)
        elif self.pages_loaded >= self.max_pages:
            self.logger.info("Maximum number of pages loaded. Stopping.")

    def parse_article(self, response):
        if response.css("div.RichTextArticleBody-body.RichTextBody"):
            self.articles[response.url] = {} # in case you need to store extra information about the article, add to dictionary
            self.logger.info(f"Article found and added: {response.url}")

    def closed(self, reason):
        with open("articles.json", "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Saved articles to articles.json")

# Main spider that scrapes the articles and runs the tests
class ArticleSpider(scrapy.Spider):
    name = "article"

    def __init__(self, *args, **kwargs):
        super(ArticleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        self.logger.warning(f"{'='*50} STARTING TESTS {'='*50}")
        if TEST_SCRAPED_URLS:
            with open("articles.json", "r", encoding="utf-8") as f:
                articles = json.load(f).keys()
        else:
            articles = ARTICLES.keys()

        for url in articles:
            yield scrapy.Request(
                url,
                self.parse,
            )

    def parse(self, response):
        url = response.url
        article = response.css("div.RichTextArticleBody-body.RichTextBody")
        if article:
            try:
                tests = clean_data_and_run_tests(self, url, article)
            except Exception as e:
                self.logger.critical(f"UNEXPECTED ERROR: {e}")
        else:
            self.logger.error(f"No Article found at {url}")
        yield None       


# Use to test authentication through Scrapy Middleware (LoginMiddleware)
class TestAuthSpider(scrapy.Spider):
    name = "test-auth"

    start_urls = ["https://qa.brightspot.chronicle.com/article/how-to-get-your-students-to-read"]

    def parse(self, response):
        self.logger.info("Visited URL: %s", response.url)
        self.logger.info("Response Status: %d", response.status)

        page_title = response.css("title::text").get()
        if page_title:
            self.logger.info("Page Title: %s", page_title)
        else:
            self.logger.warning("No title found. Auth might have failed.")





# for element in article.xpath("./*"):
    # tag_name = element.root.tag
    # tag_text = element.get()
    # tag_content = json.dumps(element.get())
    # print(f"Tag Name: {tag_name}")
    # print(f"Tag Text: {tag_text}")
    # print(f"Tag Content: {tag_content}")
    # print("\n")

