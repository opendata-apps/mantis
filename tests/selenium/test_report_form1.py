from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

import os

opts = Options()
opts.add_argument("--headless")
driver = Firefox(options=opts)


def test_impressum():
    # not finished yet, only a strating point
    try:
        wait = WebDriverWait(driver, 10)
        driver.implicitly_wait(10)
        driver.get("http://localhost:5000/report")
        # Step I

        driver.find_element(By.ID, "picture").send_keys(
            os.getcwd() + "/tests/selenium/mantis-test.webp"
        )
        driver.find_element(By.ID, "longitude").send_keys("53.57620")
        driver.find_element(By.ID, "latitude").send_keys("8.58582")
        driver.find_element(By.ID, "latitude").send_keys(Keys.TAB)
        driver.find_element(By.CLASS_NAME, "step")

    finally:

        driver.quit()
