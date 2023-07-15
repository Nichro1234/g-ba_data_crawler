import logging
import time
import json

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
            html_results = pdf_crawler.request_assessment_url(i["URL"])
            i["pdf_url"] = html_results[0]
            i["company_name"] = html_results[1]
            time.sleep(2)
            pdf_crawler.download_and_store_pdf(i["id"], i["pdf_url"])
            time.sleep(1)
            i["valid"] = True
        except IndexError:
            logging.error("Decision PDF not available for " + i["drug_name"] + "-" + i["id"] + ", download skipped")
            i["valid"] = False
            pass

    filtered_valid_results = list(filter(lambda x: x["valid"], filtered_valid_results))

    pdf_parser.initialize()
    for i in filtered_valid_results:
        try:
            tables = pdf_parser.parse_target_pdf(i["id"])

            survival = table_info_extractor.get_endpoint_data(tables["Mortalität"], "Gesamtüberleben")
            i["hr_survival"] = survival[0]
            i["p_value_survival"] = survival[1]

            pfs = table_info_extractor.get_endpoint_data(tables["Morbidität"], "PFS")
            i["hr_pfs"] = pfs[0]
            i["p_value_pfs"] = pfs[1]

            i["pdf_format_supported"] = True
        except ValueError:
            i["pdf_format_supported"] = False

    with open('convert.txt', 'w') as convert_file:
        convert_file.write(json.dumps(filtered_valid_results))

    print("end")
    print(1234)
