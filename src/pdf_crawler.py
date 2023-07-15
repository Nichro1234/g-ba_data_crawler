import io
import logging
import os

import configparser
import pypdf
import requests
from bs4 import BeautifulSoup
import utils

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def request_assessment_url(url_of_assessment):
    # For the webpage to load normally
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36",
    }

    conn = requests.get(url_of_assessment, headers=headers)
    doc = BeautifulSoup(conn.text, features='lxml')
    pdf_path = doc.select("*[id='beschluesse'] div div a")[0].attrs["href"]
    company = utils.match_company_name(conn.text)

    return ["https://g-ba.de" + pdf_path, company]


def download_and_store_pdf(assessment_id, pdf_url):
    logging.info("Crawling pdf for " + assessment_id)
    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")

    if os.path.exists(pdf_storage_path):
        print("pdf exists")
    else:
        t = requests.get(pdf_url, stream=True)
        pdf = pypdf.PdfReader(io.BytesIO(t.content))

        # pdf_path = os.path.join(pdf_storage_path, pdf_url[0] + ".pdf")
        # pypdf.PdfWriter(open(pdf_path, "w"), pdf)

        pdf_path = os.path.join(pdf_storage_path, assessment_id + ".pdf")
        pypdf.PdfWriter(open(pdf_path, "w"), pdf).write(pdf_path)


def initialize():
    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")
    utils.check_create_path(pdf_storage_path, path_of="pdf")
