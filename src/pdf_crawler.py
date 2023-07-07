import requests
import configparser
import re
import time
import logging
import pypdf
import io
import os
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def filter_target_ICD(xml_results):
    target_icd = config.get("pdf_crawler", "icd")
    # This is to allow for both "ICD,ICD" and "ICD, ICD"
    target_icd_list = re.split(",\\s?", target_icd)

    return [i for i in xml_results if any(a in i["ICD"] for a in target_icd_list)]


def extract_pdf_url(url_of_assessment):
    # For the webpage to load normally
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Sec-Ch-Ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }

    conn = requests.get(url_of_assessment, headers=headers)
    doc = BeautifulSoup(conn.text, features='lxml')
    pdf_path = doc.select("*[id='beschluesse'] div div a")[0].attrs["href"]

    return "https://g-ba.de" + pdf_path


def download_and_store_pdf(pdf_url):
    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")

    t = requests.get(pdf_url[1], stream=True)
    pdf = pypdf.PdfReader(io.BytesIO(t.content))

    pdf_path = os.path.join(pdf_storage_path, pdf_url[0] + ".pdf")
    pypdf.PdfWriter(open(pdf_path, "w"), pdf)

    pdf_path = os.path.join(pdf_storage_path, pdf_url[0] + ".pdf")
    pypdf.PdfWriter(open(pdf_path, "w"), pdf).write(pdf_path)


def start_crawl(xml_results):
    xml_results = filter_target_ICD(xml_results)

    pdf_urls = dict()
    for i in xml_results:
        try:
            pdf_urls[i["drug_name"]] = extract_pdf_url(i["URL"])
            time.sleep(2)
        except IndexError:
            logging.error("Decision PDF not available for this drug")
            pass

    for pdf_url in pdf_urls.items():
        download_and_store_pdf(pdf_url)
