import scrapy
import json
from chronicle.parse_parameters import ARTICLES, VERBOSE
from chronicle.utils import CleanData, RunTests

class ArticleSpider(scrapy.Spider):
    name = "article"

    def __init__(self, *args, **kwargs):
        super(ArticleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in ARTICLES.keys():
            frequency = ARTICLES[url]["frequency"]
            offset = ARTICLES[url]["offset"]
            yield scrapy.Request(
                url,
                self.parse,
                meta={"url_processing": url, "frequency": frequency, "offset": offset}
            )

    def parse(self, response):
        url_processing = response.meta["url_processing"]
        frequency = response.meta["frequency"]
        offset = response.meta["offset"]

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
            for freq in range(1, 8):
                for off in range(1, 8):
                    # Clean data
                    clean = CleanData(spider=self, tags=tag_names, htmls=tag_contents)
                    clean.data.update({
                        "offset": off,
                        "frequency": freq,
                        "url": url_processing
                    })
                    tests = RunTests(spider=self, data=clean.data)
                    if tests.report.get('status'):
                        self.logger.warning(f"ALL TESTS PASSED. URL: {url_processing}, offset: {off}, frequency: {freq}")
                    else:
                        if VERBOSE:
                            self.logger.critical(f"TESTS FAILED. URL: {url_processing}, offset: {off}, frequency: {freq}. DETAILS: {tests.report.get('details')}")

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

