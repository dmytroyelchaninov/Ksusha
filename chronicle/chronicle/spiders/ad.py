import scrapy
import json
from chronicle.parse_parameters import ARTICLES
from chronicle.utils import clean_data_and_run_tests

class ArticleSpider(scrapy.Spider):
    name = "article"

    def __init__(self, *args, **kwargs):
        super(ArticleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in ARTICLES.keys():
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
    name = "test_auth"

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
