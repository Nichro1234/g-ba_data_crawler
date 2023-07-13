import re

CLEANER = re.compile('<.*?>')


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

    # Since the original Deutsch word beträchtlich may have problem processing the ä,
    # we use a regex to process this part
    if re.findall(r"betr\S*chtlich", deutsch_benefit):
        return "Considerable Benefit"

    if "nicht quantifizierbar" in deutsch_benefit:
        return "Not Quantifiable"
    if "erheblich" in deutsch_benefit:
        return "Considerable Benefit"
    if "gering" in deutsch_benefit:
        return "Minor Benefit"