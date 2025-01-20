### TO TEST ADS:

1. Install scrapy, selenium dependancies: pip install scrapy selenium webdriver-manager python-dotenv
2. INSTALL CHROME!
   Scrapy through selenium will launch chrome browser to login and store cookies for subsequent requests.
3. Update ARTICLES to parse in parse_parameters.py.
4. Update VERBOSE along with articles. True means detailed logs, mostly for debugging purposes.
5. Add .env in chronicle/chronicle/ and put there QA credentials (don't use ' ' or " "!):

   LOGIN_EMAIL=1234@gmilo.com

   LOGIN_PASSWORD=1234

6. Go to chronicle/ (where scrapy.cfg) in bash and run:
   scrapy crawl article

Spider could be easily extended to scrap articles throughout website and process them asynchronously.
Also, could be sat to scrap and run tests in real-time.

If you face problem with logging in, try to increase time.sleep() in middlewares.LoginMiddleware.

Enjoy logs :)
