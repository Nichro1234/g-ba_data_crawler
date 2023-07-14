import logging
import time

import pandas as pd

import pdf_crawler
import pdf_parser
import utils
import xml_handler
import table_info_extractor

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

    results = xml_handler.initialize()
    filtered_ICD_results = utils.filter_target_ICD(results)
    filtered_valid_results = utils.filter_invalid_entries(filtered_ICD_results)
    xml_derived_df = pd.DataFrame.from_records(results)

    pdf_crawler.initialize()
    for i in filtered_valid_results:
        try:
            i["pdf_url"] = pdf_crawler.request_pdf_url(i["URL"])
            time.sleep(2)
            pdf_crawler.download_and_store_pdf(i["drug_name"], i["pdf_url"])
        except IndexError:
            logging.error("Decision PDF not available for " + i["drug_name"] + ", download skipped")
            pass

    pdf_parser.initialize()
    for i in filtered_valid_results:
        tables = pdf_parser.parse_target_pdf(i["drug_name"])
        survival = table_info_extractor.get_endpoint_data(tables["Mortalität "], "Gesamtüberleben")
        print(survival)
