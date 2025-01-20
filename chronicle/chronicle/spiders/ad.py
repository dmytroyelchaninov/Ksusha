import scrapy
import json
from chronicle.parse_parameters import ARTICLES
from chronicle.utils import CleanData, RunTests

class ArticleSpider(scrapy.Spider):
    name = "article"

    def __init__(self, *args, **kwargs):
        self.url_processing = None
        self.frequency = None
        self.offset = None
        super(ArticleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in ARTICLES.keys():
            self.url_processing = url
            self.frequency = ARTICLES[url]["frequency"]
            self.offset = ARTICLES[url]["offset"]
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        article_body = response.css("div.RichTextArticleBody-body.RichTextBody")

        if article_body:
            children = article_body.xpath("./*")
            tag_names = []
            tag_contents = []

            for child in children:
                tag_name = child.root.tag
                inner_html = child.get()
                tag_names.append(tag_name)
                tag_contents.append(json.dumps(inner_html)) # To avoid "" '' issues
                # tag_contents.append(inner_html)
            self.logger.info(f"Extracted tag names: {tag_names}")
            self.logger.info(f"Extracted tag contents: {tag_contents}")

            # Clean data
            clean = CleanData(spider=self, tags=tag_names, htmls=tag_contents)
            clean.data.update({
                "offset": self.offset,
                "frequency": self.frequency,
                "url": self.url_processing
            })
            tests = RunTests(spider=self, data=clean.data)
            if tests.report.get('status'):
                self.logger.warning(f"ALL TESTS PASSED. URL: {self.url_processing}, offset: {self.offset}, frequency: {self.frequency}")
            else:
                self.logger.critical(f"TESTS FAILED. URL: {self.url_processing}, OFFSET: {self.offset}, FREQUENCY: {self.frequency}. DETAILS: {tests.report.get('details')}")
            yield {
                "url": tests.report.get('url'),
                "status": tests.report.get('status'),
                "details": tests.report.get('details')
            }
        else:
            self.logger.warning("No article body found.")


# Used to test authentication through Scrapy Middleware (LoginMiddleware)
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

