#!/usr/bin/env python3

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

opts = Options()
# alt: opts.headless = True
opts.add_argument("--headless")
driver = Firefox(options=opts)

try:

    driver.get('http://localhost:5000')
    title = driver.title
    content = driver.page_source
    assert '<title>Mantis Religiosa Beobachtungen | Mitmachprojekt | Gottesanbeterin Gesucht</title>' in content

finally:

    driver.quit()
