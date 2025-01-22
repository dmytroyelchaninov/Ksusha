import scrapy
import time
from scrapy.exceptions import CloseSpider
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from scrapy import signals
from chronicle.logger import LogFilter
import logging
import os 
from dotenv import load_dotenv
load_dotenv()


# Note: all credentials must be stored in .env file (environment variables), same level as this file
# Otherwise, your credentials will be exposed in the codebase
class LoggingMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        instance = cls()
        is_disabled = crawler.settings.getbool('DEFAULT_LOGS_DISABLED', True)
        log_filter = LogFilter(is_disabled)

        logging.getLogger().addFilter(log_filter)
        crawler.signals.connect(instance.spider_opened, signal=scrapy.signals.spider_opened)

        return instance

    def spider_opened(self, spider):
        spider.logger.info("Logging filter applied")


class LoginMiddleware:
    def __init__(self):
        self.logged_in = False
        self.cookies = {}
        self.driver = None

    def start_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def process_request(self, request, spider):
        if self.logged_in:
            request.cookies = {cookie['name']: cookie['value'] for cookie in self.cookies}
            return None

        if not self.logged_in:
            self.start_driver()
            spider.logger.info("Starting login")
            try:
                self.login_user(spider)
            except Exception as e:
                spider.logger.critical(f"Login failed: {e}")
                raise CloseSpider("LOGIN FAILED")
            finally:
                self.stop_driver()
        return None

    def login_user(self, spider):
        self.driver.get("https://qa.brightspot.chronicle.com/")
        wait = WebDriverWait(self.driver, 10)

        sign_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Sign In']")))
        sign_in_button.click()
        
        time.sleep(2) # CRUCIAL: Wait for the login modal to appear

        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="1-email"]')))
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="1-password"]')))
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="1-submit"]')))

        email_input.clear()
        password_input.clear()

        email = os.getenv("LOGIN_EMAIL")
        password = os.getenv("LOGIN_PASSWORD")

        email_input.send_keys(email)
        password_input.send_keys(password)
        submit_button.click()

        user_menu = wait.until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class,'user-menu-trigger')]"))
        ) # Just like in ROBOT
        if user_menu:
            spider.logger.info("Login successful")
            self.logged_in = True
            self.cookies = self.driver.get_cookies()
        else:
            raise CloseSpider("Login failed")


# Some default middlewares from request/response handling, i will keep them default, but they are very useful tho
# Override some methods for custom middleware behavior
class ChronicleSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class ChronicleDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
