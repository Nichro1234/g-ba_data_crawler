import re
import os
import configparser

import logging

# Compile some regex in advance to reduce runtime compilation cost
CLEANER = re.compile('<.*?>')

# used to match beträchtlich
BETRA_MATCHER = re.compile("betr\\S*chtlich")
COMPANY_MATCHER = re.compile(r"<strong>Pharmazeutischer Unternehmer:</strong>.*")

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def cleanhtml(raw_html):
    clean_text = re.sub(CLEANER, '', raw_html)
    remove_line_break = re.sub(r"\n", "", clean_text)
    return remove_line_break


def map_arrow_to_value(arrow):
    if arrow == "n.b.":
        return "Not Assessed"
    if arrow == "&Oslash;":
        return "No Data"
    if arrow == "&harr;":
        return "No Difference"

    if arrow == "&uarr;&uarr;":
        return "Significant Positive Effect"
    if arrow == "&darr;&darr;":
        return "Significant Positive Effect"
    if arrow == "&uarr;":
        return "Significant Positive Effect"
    if arrow == "&darr;":
        return "Significant Positive Effect"


def translate_benefit(deutsch_benefit):
    if "nicht belegt" in deutsch_benefit:
        return "No Proven Benefit"

    # Since the original Deutsch word beträchtlich may cause problem when processing ä,
    # we use a regex to process this word
    if re.findall(BETRA_MATCHER, deutsch_benefit):
        return "Considerable Benefit"

    if "nicht quantifizierbar" in deutsch_benefit:
        return "Non-Quantifiable Benefit"
    if "erheblich" in deutsch_benefit:
        return "Considerable Benefit"
    if "gering" in deutsch_benefit:
        return "Minor Additional Benefit"


def list_remove_duplicate(input_list):
    result = []
    for i in input_list:
        if i not in result:
            result.append(i)
    return result


def check_create_path(target_path, path_of):
    if not os.path.exists(target_path):
        os.mkdir(target_path)
        logging.info(path_of + " storage path does not exist, creating folder and scraping...")
        return False
    return True


def filter_target_ICD(xml_results):
    target_icd = config.get("pdf_crawler", "icd")
    # This is to allow for both "ICD,ICD" and "ICD, ICD"
    target_icd_list = re.split(",\\s?", target_icd)

    result = []
    for i in xml_results:
        include = False
        for icd in i["ICD"]:
            for j in target_icd_list:
                if icd.startswith(j):
                    include = True
        if include:
            result.append(i)
    return result


def filter_invalid_entries(xml_results):
    results = []

    for i in xml_results:
        metrics = [i["mortality"], i["morbidity"], i["quality_of_life"], i["side_effects"]]
        for j in metrics:
            if j not in ["No Data", "Not Assessed"]:
                results.append(i)
                break
    return results


def match_company_name(html_text):
    results = re.findall(COMPANY_MATCHER, html_text)
    if results:
        cleaned_str = cleanhtml(results[0])
        return cleaned_str.split(":")[1]

    else:
        return "Not Found"
