### FIRST STEPS:

1. Install scrapy, selenium dependancies: pip install scrapy selenium webdriver-manager python-dotenv
2. INSTALL CHROME!
   Scrapy through selenium will launch chrome browser to login and store cookies for subsequent requests.
3. Add .env in chronicle/chronicle/ and put there QA credentials (don't use ' ' or " "!):

   LOGIN_EMAIL=1234@gmilo.com

   LOGIN_PASSWORD=1234

4. Go to chronicle/ (where scrapy.cfg) in bash and run:
   scrapy crawl article

### TO SCRAP ALL URLS, CONTAINING ARTICLES AND BLOGS:

### TO TEST ADS:

1. You can use prescraped urls or change them manually:
   1. Automated testing
1. Update ARTICLES to parse in parse_parameters.py, for manually selected articles.
1. Update VERBOSE along with articles. True means detailed logs, mostly for debugging purposes.

For testing auth on the website use "test_auth" spider. If successful, it will say in logs and print message in terminal.
spider crawl test_auth
If you face problem with logging in, try to increase time.sleep() in middlewares.LoginMiddleware.

Enjoy Scrapy (/ˈskreɪpaɪ/)

Docs:
https://docs.scrapy.org/en/latest/intro/overview.html
