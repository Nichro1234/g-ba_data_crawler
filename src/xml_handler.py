import requests
import os
import configparser
import datetime
import xmltodict
from utils import cleanhtml

config = configparser.ConfigParser()


def need_update():
    config.read("config.ini", encoding="utf-8")
    last_crawled = config.get('xml_getter', "last_crawled")

    if last_crawled == "":
        return True
    else:
        last_crawled_list = list(map(int, last_crawled.split("-")))
        last_crawled_date = datetime.datetime(last_crawled_list[0], last_crawled_list[1], last_crawled_list[2])
        date_diff = datetime.datetime.today() - last_crawled_date
        if date_diff.days > 10:
            return True
    return False


def get_xml(perma_link):
    xml_file = requests.get(perma_link)

    filename = xml_file.headers["x-amz-meta-filename"]
    xml_content = xml_file.text
    xml_storage_path = "..\\xml_storage"

    with open(os.path.join(xml_storage_path, filename), "w", encoding="utf-8") as f:
        f.write(xml_content)

    today_date = str(datetime.datetime.today().date())
    config.set("xml_getter", "last_crawled", today_date)
    config.write(open("config.ini", "w", encoding="utf-8"))


def read_xml(path_to_xml):
    with open(path_to_xml, "r") as f:
        xml_string = f.read()
    result = xmltodict.parse(xml_string)
    return result['BE_COLLECTION']['BE']


def extract_endpoint_results(info_dict):
    _temp = dict()
    _temp["benefit"] = info_dict["ZVT_ZN"]["ZN_A"]["@value"]
    _temp["drug_name"] = info_dict["WS_BEW"]['NAME_WS_BEW']["@value"]
    _temp["patient_group"] = cleanhtml(info_dict["NAME_PAT_GR"])

    icd_dict = info_dict["ICD"]
    try:
        _temp["ICD"] = [i["ID_ICD"]["@value"] for i in icd_dict]
    except TypeError:
        _temp["ICD"] = [icd_dict["ID_ICD"]["@value"]]

    _temp["mortality"] = info_dict['ZSF_EP_MORT']['EP_MORT_GRAF']["@value"]
    _temp["morbidity"] = info_dict['ZSF_EP_MORB']['EP_MORB_GRAF']["@value"]
    _temp["quality_of_life"] = info_dict['ZSF_EP_LEBQ']['EP_LEBQ_GRAF']["@value"]
    _temp["side_effects"] = info_dict['ZSF_EP_UE']['EP_UE_GRAF']["@value"]
    return _temp


def parse_xml(data):
    result_list = []

    for i in data:
        benefit_assessment = dict()
        benefit_assessment["URL"] = i['URL']["@value"]

        try:
            benefit_assessment["is_orphan"] = i["ZUL"]["SOND_ZUL_ORPHAN"]["@value"]
        except TypeError:
            benefit_assessment["is_orphan"] = i["ZUL"][0]["SOND_ZUL_ORPHAN"]["@value"]

        endpoint_results = []
        if type(i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR']) != list:
            endpoint_results.append(benefit_assessment|extract_endpoint_results(i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR']))
        else:
            for j in i['PAT_GR_INFO_COLLECTION']['ID_PAT_GR']:
                endpoint_results.append(benefit_assessment|extract_endpoint_results(j))

        result_list += endpoint_results

    return result_list


if __name__ == '__main__':
    print("Start crawling...")
    if need_update():
        get_xml(config.get("xml_getter", "perma_link"))
