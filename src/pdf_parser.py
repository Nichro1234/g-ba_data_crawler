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

    # Show only the tables related to the four measures
    for title, block in iter_block_items(doc):
        if title in ["Mortalität ", "Morbidität ", "Gesundheitsbezogene Lebensqualität ", "Nebenwirkungen "]:
            if ('Endpunkt ', 'Endpunkt ') in block[0].items():

                # Not a good solution. Currently, we assume that only the table heads are going to be the same for
                # tables that crosses pages, which is not the case
                assessment_detail_tables[title] = utils.list_remove_duplicate(block)
    return assessment_detail_tables


def init():
    temp_storage_path = config.get("pdf_parser", "temp_path")
    utils.check_create_path(temp_storage_path, path_of="docx")


# Test Code
if __name__ == '__main__':
    init()

    pdf_storage_path = config.get("pdf_crawler", "pdf_storage_path")
    pdf_list = os.listdir(pdf_storage_path)
    pdf_list = [i for i in pdf_list if i.endswith(".pdf")]
    import table_info_extractor

    for pdf_file in pdf_list:
        docx_path = convert_pdf(os.path.join(pdf_storage_path, pdf_file))
        tables = extract_tables(docx_path)

        result = {}
        for endpoint_category, table in tables.items():
            category_table = table_info_extractor.derive_metric_names(table)
            cleaned_table = table_info_extractor.clean_up_table(category_table)

            result[endpoint_category] = cleaned_table




















