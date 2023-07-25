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

    features = []
    with open("target_features", "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i in lines:
        features.append(i.replace("\n", "").split(","))

    pdf_parser.initialize()
    for i, entry in enumerate(filtered_valid_results):
        try:
            tables = pdf_parser.parse_target_pdf(entry["id"])
            entry["pdf_format_supported"] = True

        # temporary solution for now. It is not appropriate to use a bare except clause without handling
        # specifically certain types of error
        except:
            entry["pdf_format_supported"] = False
            continue

        for j in features:
            try:
                _res = table_info_extractor.get_endpoint_data(tables[j[1]], j[0])
                entry["hr_" + j[2]] = _res[0]
                entry["p_value" + j[2]] = _res[1]
            except:
                entry["hr_" + j[2]] = "Data not Found"
                entry["p_value" + j[2]] = "Data not Found"

    with open('convert.txt', 'w', encoding="utf-8") as convert_file:
        convert_file.write(json.dumps(filtered_valid_results))

    print("end")
    print(1234)
