import re

CLEANER = re.compile('<.*?>')


def cleanhtml(raw_html):
    clean_text = re.sub(CLEANER, '', raw_html)
    return clean_text
