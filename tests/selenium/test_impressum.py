#!/usr/bin/env python3

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

opts = Options()
opts.add_argument("--headless")
driver = Firefox(options=opts)


def test_impressum():
    try:

        driver.get('http://localhost:5000/impressum')
        title = driver.title
        content = driver.page_source
        assert """<h1 class="mb-6 text-4xl font-bold text-center text-white md:text-6xl lg:text-left">
                  Impressum
                </h1>""" in content

    finally:

        driver.quit()
