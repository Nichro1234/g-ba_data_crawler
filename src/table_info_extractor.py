import re


def extract_data_from_table(table):
    for row in table:
        if row['Endpunkt '] == "" or row['Endpunkt '] == "Metaanalyse":
            target = row["Intervention vs. Kontrolle"]
            list_of_data = re.split(r"\s", target)
            list_of_data = [i for i in list_of_data if i != ""]
            return list_of_data[0], list_of_data[-1]























