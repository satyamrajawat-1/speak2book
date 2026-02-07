import time
import datetime
import base64
import os
import tempfile
import webbrowser
import urllib.request

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


def handle_aadhaar_popup(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='OK']"))
        ).click()
        print("Aadhaar alert popup accepted.")
        time.sleep(1)
    except TimeoutException:
        print("No Aadhaar alert popup found.")


# ---------------- Login ----------------
def login_irctc(driver, username, password, timeout=10):
    wait = WebDriverWait(driver, timeout)

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'LOGIN')]"))
    ).click()
    print("Login button clicked.")
    time.sleep(3)

    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='userid']"))
    ).send_keys(username)

    driver.find_element(
        By.CSS_SELECTOR, "input[formcontrolname='password']"
    ).send_keys(password)

    driver.find_element(
        By.XPATH, "//button[contains(text(),'SIGN IN')]"
    ).click()

    print("Login form submitted.")
    time.sleep(5)
