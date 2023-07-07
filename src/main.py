import xml_handler
import pdf_crawler

if __name__ == '__main__':
    results = xml_handler.initialize()
    pdf_crawler.start_crawl(results)

