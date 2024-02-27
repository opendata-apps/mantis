#!/usr/bin/env python3

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

opts = Options()
opts.add_argument("--headless")
browser = Firefox(options=opts)


def test_links():
    try:

        browser.get("http://localhost:5000")
        elements = browser.find_elements(By.TAG_NAME, "a")
        for e in elements:
            gesucht = "Problem melder"
            gefunden = e.text
            if gesucht in gefunden:  # and (len(gefunden) == len(gesucht)):
                assert e.text == gefunden

    finally:

        browser.quit()
