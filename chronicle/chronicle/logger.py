import logging

class LogFilter(logging.Filter):
    def __init__(self, spider_logs_only):
        self.spider_logs_only = spider_logs_only
        super().__init__()

    def filter(self, record):
        if self.spider_logs_only:
            return record.name.startswith("article") or record.name.startswith("chronicle")
        return True