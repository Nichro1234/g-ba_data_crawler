import re
import copy


def derive_metric_names(table):
    _table = copy.deepcopy(table)
    for i, row in enumerate(_table):
        if len(set(row.values())) == 1:
            _table[i] = next(iter(set(row.values())))
    return _table


def clean_up_table(table):
    prev_text = "table_head"

    result = {}
    table_buffer = []

    for i, row in enumerate(table):
        if type(row) == str and table_buffer:
            result[prev_text] = table_buffer
            prev_text = row
            table_buffer = []

        else:
            table_buffer.append(row)
    result[prev_text] = table_buffer
    return result


def process_endpoint_result_str(result_str):
    _result = re.split(r"\n?[\(\[].*[\)\]]", result_str)
    num_and_space_only = [re.sub(r"[^0-9, ]", "", i) for i in _result]
    num_only = []
    for i in num_and_space_only:
        num_only += i.split(" ")
    return [i for i in num_only if i != ""]


def get_endpoint_data(table, endpoint):
    if endpoint in table.keys():
        endpoint_data = table[endpoint]
        return crawl_multi_study_assessment(endpoint_data)

    else:
        for sub_table in table.values():
            for row in sub_table:
                if row["Endpunkt "] == endpoint:
                    return process_endpoint_result_str(row["Intervention vs. Kontrolle"])
    return "Data not Found"


def crawl_multi_study_assessment(endpoint_data):
    for row in endpoint_data:
        if row['Endpunkt '] == "" or row['Endpunkt '] == "Metaanalyse":
            target = row["Intervention vs. Kontrolle"]
            list_of_data = process_endpoint_result_str(target)
            return list_of_data[0], list_of_data[1]
    target = endpoint_data[-1]["Intervention vs. Kontrolle"]
    list_of_data = process_endpoint_result_str(target)
    return list_of_data[0], list_of_data[1]
