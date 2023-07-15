import configparser
import os
import copy
import re

import docx
import utils
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from pdf2docx import Converter
import logging
from itertools import chain

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def convert_pdf(pdf_path):
    cv = Converter(pdf_path)
    temp_path = config.get("pdf_parser", "temp_path")
    docx_path = os.path.join(temp_path, pdf_path.split("\\")[-1] + '.docx')
    print(docx_path)

    cv.convert(docx_path, start=0, end=None)
    cv.close()
    return docx_path


def iter_block_items(parent):
    table_buffer = []

    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc

    prev_para_text = ""
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            paragraph_text = Paragraph(child, parent).text
            paragraph_text = re.sub(r"\s?\(.*\)", "", paragraph_text)
            paragraph_text = paragraph_text.rstrip()
            # tackle problems with tables that crosses pages
            # When a table crosses pages, there will be two cases.
            # 1. the table is followed by page number and empty text
            # 2. the table is followed by notes at the end of the page, often led by a single number
            if paragraph_text == "" or paragraph_text.replace(" ", "").isnumeric():
                continue
            elif re.match(r"\d .", paragraph_text):
                continue
            else:
                if table_buffer:
                    yield prev_para_text, table_buffer
                    table_buffer = []

                if not re.match(r"\(.*\)", paragraph_text):
                    prev_para_text = paragraph_text
                else:
                    print(123)
        elif isinstance(child, CT_Tbl):
            table = Table(child, parent)
            table_buffer += table_to_dict(table)


def table_to_dict(table):
    data = []
    for i, row in enumerate(table.rows):
        text = (cell.text.rstrip() for cell in row.cells)
        row_data = tuple(text)
        data.append(row_data)
    return data


def extract_tables(docx_path):
    doc = docx.Document(docx_path)
    result = extract_pdf_layout_0(doc)

    if result != {}:
        return result

    extract_pdf_layout_1(doc)


def extract_pdf_layout_0(doc: docx.Document):
    assessment_detail_tables = {}
    # Show only the tables related to the four measures
    for title, block in iter_block_items(doc):
        if title in ["Mortalität", "Morbidität", "Gesundheitsbezogene Lebensqualität", "Nebenwirkungen"]:
            # Not a good solution. Currently, we assume that only the table heads are going to be the same for
            # tables that crosses pages, which is not the case
            assessment_detail_tables[title] = utils.list_remove_duplicate(block)
    return assessment_detail_tables


def extract_pdf_layout_1(doc: docx.Document):
    keywords = ["Mortalität", "Morbidität", "Gesundheitsbezogene Lebensqualität", "Nebenwirkungen"]

    for title, block in iter_block_items(doc):
        if all(keyword in chain(*block) for keyword in keywords):
            print(block)
            break
    raise ValueError


def initialize():
    temp_storage_path = config.get("pdf_parser", "temp_path")
    utils.check_create_path(temp_storage_path, path_of="docx")


def derive_metric_names(table):
    _table = copy.deepcopy(table)
    for i, row in enumerate(_table):
        if len(set(row)) == 1:
            _table[i] = next(iter(set(row)))
    return _table


def clean_up_table(table):
    prev_text = "table_head"

    result = {}
    table_buffer = []

    for i, row in enumerate(table):
        if type(row) == str:
            if table_buffer:
                result[prev_text] = table_buffer
                prev_text = row
                table_buffer = []
            else:
                prev_text = row
        else:
            table_buffer.append(row)
    result[prev_text] = table_buffer
    return result


def parse_target_pdf(medicine_name):
    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")

    docx_path = convert_pdf(os.path.join(pdf_storage_path, medicine_name + ".pdf"))
    tables = extract_tables(docx_path)

    result = {}
    for endpoint_category, table in tables.items():
        category_table = derive_metric_names(table)
        cleaned_table = clean_up_table(category_table)

        result[endpoint_category] = cleaned_table
    return result


# Test Code
if __name__ == '__main__':
    initialize()






















