import time
from datetime import datetime
import undetected_chromedriver as uc
import base64
import os
import tempfile
import webbrowser
import urllib.request
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from irctc import handle_aadhaar_popup,login_irctc,set_station,select_class,select_date,click_search_trains,select_class_and_book,confirm_food_dialog,fill_passenger_details,handle_captcha_and_continue,handle_payment_selection

from extension import inject_chatbot,load_global_json



cond_search=False
cond_booknow=False
cond_passfill=False

# --- Helpers ---
def split_date_str(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")


def update_irctc_form(driver):
    global cond_search
    """Read JSON and fill available slots in IRCTC form"""
    data = load_global_json()
    slots = data.get("slots", {})  # <-- use "slots" key, not "last_intent"

    from_city = slots.get("from_city")
    to_city = slots.get("to_city")
    journey_date = slots.get("journey_date")
    travel_class = slots.get("class")

    if from_city and to_city and journey_date:
        cond_search=True
        set_station(driver, from_city, "From")
        set_station(driver, to_city, "To")
        select_date(driver, split_date_str(journey_date))
        if travel_class:
            class_map = {
                "SL": "Sleeper (SL)",
                "3A": "AC 3 Tier (3A)",
                "2A": "AC 2 Tier (2A)",
                "1A": "AC First Class (1A)"
            }
            if travel_class in class_map:
                select_class(driver, class_map[travel_class])
        click_search_trains(driver)
        print(f"IRCTC updated: {from_city} → {to_city} on {journey_date} ({travel_class})")

def book_train(driver):
    global cond_booknow
    data=load_global_json()
    slots =data.get("slots", {})  
    train_number = slots.get("train_no")
    travel_class = slots.get("class")
    if train_number and travel_class:
        cond_booknow=True
        class_map = {
                "SL": "Sleeper (SL)",
                "3A": "AC 3 Tier (3A)",
                "2A": "AC 2 Tier (2A)",
                "1A": "AC First Class (1A)"
            }
        select_class_and_book(driver,train_number,class_map[travel_class])
        print(f"IRCTC BOOK now clicked : with train number {train_number} and class is {travel_class}")


def pass_page(driver):
    global cond_passfill
    data=load_global_json()
    slots=data.get("slota",{})
    name=slots.get("passenger_name")
    age=slots.get("passenger_age")
    gender=slots.get("passenger_gender")
    mobile=slots.get("passenger_mob")
    berth=slots.get("berth_preference")
    if not berth:
        berth="Lower"
    if name and age and gender and mobile:
        cond_passfill=True
        Passenger=[
            {
            'name':name,
            'age':age,
            'gender':gender,
            'berth':berth
            }
        ]
        fill_passenger_details(driver,Passenger,mobile)
        print(f"Passeneger information filled with name : {name} , age : {age} , gender : {gender} , mobile : {mobile}")
        handle_captcha_and_continue(driver)
        print("Capacha process completed")


def checker(driver):
    global cond_booknow,cond_search,cond_passfill
    if not cond_search:
        update_irctc_form(driver)
    elif not cond_booknow:
        book_train(driver)
    elif not cond_passfill:
        pass_page(driver)
    else:
        print("Not found error")


        