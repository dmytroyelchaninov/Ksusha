import scrapy

class ArticleSpider(scrapy.Spider):
    name = "article"

    article_urls = [
        # "https://qa.brightspot.chronicle.com/article/qa-test-after-sparking-a-mass-resignation-of-nursing-professors-this-college-president-resigned-too", 
        # "https://qa.brightspot.chronicle.com/article/how-to-publish-a-timely-scholarly-book",
        "https://qa.brightspot.chronicle.com/article/how-to-get-your-students-to-read"
    ]

    def start_requests(self):
        for url in self.article_urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        article_body = response.css("div.RichTextArticleBody-body.RichTextBody")

        if article_body:
            children = article_body.xpath("./*")  # Direct children only
            tag_names = []
            tag_contents = []

            for child in children:
                tag_name = child.root.tag
                inner_html = child.get()

                tag_names.append(tag_name)
                tag_contents.append(inner_html)

            # Log or yield the dictionary
            self.logger.info(f"Extracted tag names: {tag_names}")
            self.logger.info(f"Extracted tag contents: {tag_contents}")
            yield {"url": response.url, "tag_names": tag_names, "tag_contents": tag_contents}
        else:
            self.logger.warning("No article body found.")


class TestSpider(scrapy.Spider):
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

