import configparser
import datetime
import logging
import os

import requests
import xmltodict

from utils import cleanhtml

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def need_update():
    last_crawled = config.get('xml_getter', "last_crawled")

    xml_storage_path = config.get('xml_getter', "xml_storage_path")
    if not os.path.exists(xml_storage_path):
        os.mkdir(xml_storage_path)
        logging.info("Xml storage path does not exist, creating folder and scraping...")
        return True

    if not any(a.endswith(".xml") for a in os.listdir(xml_storage_path)):
        logging.info("No xml found in the storage folder, crawling...")
        return True

    if last_crawled == "":
        logging.info("Not crawled before, crawling")
        return True
    else:
        # Check the last crawled date, if more than 10 days ago, crawl the data again
        last_crawled_list = list(map(int, last_crawled.split("-")))
        last_crawled_date = datetime.datetime(last_crawled_list[0], last_crawled_list[1], last_crawled_list[2])
        date_diff = datetime.datetime.today() - last_crawled_date
        logging.info("Xml last updated more than 10 days ago, crawling...")
        if date_diff.days > 10:
            return True
    return False


def get_xml(perma_link):
    xml_file = requests.get(perma_link)

    # The xml gives the file name designated by g-ba
    filename = xml_file.headers["x-amz-meta-filename"]
    xml_content = xml_file.text
    xml_storage_path = config.get('xml_getter', "xml_storage_path")
    filepath = os.path.join(xml_storage_path, filename)

    # We need to specify the encoding since we are dealing with German language
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Update the config file
    today_date = str(datetime.datetime.today().date())
    config.set("xml_getter", "last_crawled", today_date)
    config.write(open("config.ini", "w", encoding="utf-8"))
    logging.info("Successfully updated xml")
    return filepath


def read_xml(path_to_xml):
    with open(path_to_xml, "r", encoding="utf-8") as f:
        xml_string = f.read()

    result = xmltodict.parse(xml_string)

    # This is the place where the decision data is held
    return result['BE_COLLECTION']['BE']


def extract_endpoint_results(info_dict):
    result = dict()
    result["benefit"] = info_dict["ZVT_ZN"]["ZN_A"]["@value"]
    result["drug_name"] = info_dict["WS_BEW"]['NAME_WS_BEW']["@value"]
    result["patient_group"] = cleanhtml(info_dict["NAME_PAT_GR"])
    result["mortality"] = info_dict['ZSF_EP_MORT']['EP_MORT_GRAF']["@value"]
    result["morbidity"] = info_dict['ZSF_EP_MORB']['EP_MORB_GRAF']["@value"]
    result["quality_of_life"] = info_dict['ZSF_EP_LEBQ']['EP_LEBQ_GRAF']["@value"]
    result["side_effects"] = info_dict['ZSF_EP_UE']['EP_UE_GRAF']["@value"]

    # Some medicines have multiple ICDs, therefore, we need to deal with them separately
    icd_dict = info_dict["ICD"]
    try:
        result["ICD"] = [i["ID_ICD"]["@value"] for i in icd_dict]
    except TypeError:
        result["ICD"] = [icd_dict["ID_ICD"]["@value"]]

    return result


def find_target_xml():
    xml_storage_path = config.get('xml_getter', "xml_storage_path")

    xml_list = [i for i in os.listdir(xml_storage_path) if i.endswith(".xml")]
    xml_list.sort(reverse=True)

    return os.path.join(xml_storage_path, xml_list[0])


def parse_xml(data):
    result_list = []

    for i in data:
        benefit_assessment = dict()
        benefit_assessment["URL"] = i['URL']["@value"]

        # In a very scarce case, where the drug is assessed by multiple agencies, there will be multiple entries to the
        # ZUL section (and hence multiple assessments on whether the drug is orphan). We will use the first entry.
        try:
            benefit_assessment["is_orphan"] = i["ZUL"]["SOND_ZUL_ORPHAN"]["@value"]
        except TypeError:
            benefit_assessment["is_orphan"] = i["ZUL"][0]["SOND_ZUL_ORPHAN"]["@value"]

        endpoint_results = []

        # The | here is a way to combine the two dictionaries
        if type(i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR']) != list:
            endpoint_results.append(
                benefit_assessment | extract_endpoint_results(i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR'])
            )
        else:
            for j in i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR']:
                endpoint_results.append(benefit_assessment | extract_endpoint_results(j))

        result_list += endpoint_results

    return result_list


def initialize():
    if need_update():
        get_xml(config.get("xml_getter", "perma_link"))

    target_xml = find_target_xml()
    xml_results = parse_xml(read_xml(target_xml))
    return xml_results


# Test Code
if __name__ == '__main__':
    print("Start crawling...")
    if need_update():
        get_xml(config.get("xml_getter", "perma_link"))
    find_target_xml()
