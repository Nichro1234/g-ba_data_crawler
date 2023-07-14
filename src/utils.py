import re
import os

import logging

# Compile some regex in advance to reduce runtime compilation cost
CLEANER = re.compile('<.*?>')

# used to match beträchtlich
BETRA_MATCHER = re.compile("betr\\S*chtlich")


def cleanhtml(raw_html):
    clean_text = re.sub(CLEANER, '', raw_html)
    return clean_text


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
        return "Considerable Additional Benefit"
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