import xml_handler
import pdf_crawler

import logging

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

    results = xml_handler.initialize()
    pdf_crawler.start_crawl(results)

