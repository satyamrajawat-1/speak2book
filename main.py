import time
import datetime
import undetected_chromedriver as uc
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

from irctc import handle_aadhaar_popup,login_irctc,set_station,select_class,select_date,click_search_trains,select_class_and_book,confirm_food_dialog,fill_passenger_details,handle_captcha_and_continue,handle_payment_selection

from validation import search_trains_click
from extension import inject_chatbot

KEEP_BROWSER_OPEN = True

driver = None
try:
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = uc.Chrome(version_main=144, options=options)
    driver.get("https://www.irctc.co.in")
    time.sleep(5)

    handle_aadhaar_popup(driver)
    search_trains_click(driver)
    # login_irctc(driver, "Satyam_rajawat113", "Satyam@28312")

    # set_station(driver, "Kota", "From")
    # set_station(driver, "NDLS", "To")

    # select_class(driver, "AC 2 Tier (2A)")
    # select_date(driver, "05/03/2026")
    # click_search_trains(driver)

    # select_class_and_book(
    #     driver,
    #     train_number="12951",
    #     class_name="AC 2 Tier (2A)"
    # )

    # # --- Passenger data: edit as needed ---
    # PASSENGERS = [
    #     {"name": "Raghav Gupta", "age": 28, "gender": "M", "berth": "LB"},
    #     {"name": "Pankaj Gupta", "age": 50, "gender": "M", "berth": "UB"},
    # ]
    # MOBILE_NUMBER = "9200000075"  # edit to your contact number (10 digits)

    # # fill passenger details and continue to review/payment
    # fill_passenger_details(driver, PASSENGERS, MOBILE_NUMBER)
    # # handle captcha on review page (opens image and prompts for manual input)
    # try:
    #     ok = handle_captcha_and_continue(driver, timeout=180)
    #     if ok:
    #         print("Captcha handled; proceeding to payment page (if navigation completed).")
    #         try:
    #             paid = handle_payment_selection(driver, timeout=60)
    #             if paid:
    #                 print('Payment option chosen and pay button clicked (or attempted).')
    #             else:
    #                 print('Payment selection failed; please complete payment manually in the browser.')
    #         except Exception as e:
    #             print('Error while selecting payment option:', e)
    #     else:
    #         print("Captcha was not handled automatically. Please complete it manually in the browser.")
    # except Exception as e:
    #     print('Error while handling captcha:', e)

    # time.sleep(10000)

finally:
    if driver:
        if KEEP_BROWSER_OPEN:
            print("KEEP_BROWSER_OPEN is True — leaving browser open for manual review/payment.")
        else:
            driver.quit()