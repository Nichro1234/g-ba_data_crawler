import configparser
import os

import docx
import utils
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from pdf2docx import Converter

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def convert_pdf(pdf_path):
    cv = Converter(pdf_path)
    temp_path = config.get("pdf_parser", "temp_path")
    docx_path = os.path.join(temp_path, pdf_path + '.docx')

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
            if paragraph_text == "" or paragraph_text.replace(" ", "").isnumeric():
                continue
            else:
                if table_buffer:
                    yield prev_para_text, table_buffer
                    table_buffer = []
                prev_para_text = paragraph_text
        elif isinstance(child, CT_Tbl):
            table = Table(child, parent)
            table_buffer += table_to_dict(table)


def table_to_dict(table):
    data = []
    for i, row in enumerate(table.rows):
        text = (cell.text for cell in row.cells)

        if i == 0:
            keys = tuple(text)
            continue
        row_data = dict(zip(keys, text))
        data.append(row_data)
    return data


def extract_tables(docx_path):
    doc = docx.Document(docx_path)

    assessment_detail_tables = {}

    # Show only the tables related to the
    for title, block in iter_block_items(doc):
        if title in ["Mortalität ", "Morbidität ", "Gesundheitsbezogene Lebensqualität ", "Nebenwirkungen "]:
            if ('Endpunkt ', 'Endpunkt ') in block[0].items():
                assessment_detail_tables[title] = block
    return assessment_detail_tables


def init():
    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")
    utils.check_create_path(pdf_storage_path, path_of="pdf")

