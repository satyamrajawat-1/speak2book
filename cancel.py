import time
import datetime
import base64
import os
import tempfile
import webbrowser
import urllib.request

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

def navigate_to_booked_ticket_history(driver, timeout=12):
    """Hover over the top navigation to open:
    My Account -> My Transactions -> Booked Ticket History

    This performs hover (ActionChains.move_to_element) and falls back to clicking elements
    when needed. Returns True on success, False otherwise.

    Reference: selectors inspired by the project's `book.py` and UI structure in `home.html`.
    """
    wait = WebDriverWait(driver, timeout)
    actions = ActionChains(driver)

    try:
        # Find 'My Account' menu entry (case-insensitive match)
        my_account = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='my account' or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'my account')]")
            )
        )
    except TimeoutException:
        # Try alternate selector that might be visible as capital letters
        try:
            my_account = wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(., 'MY ACCOUNT') or contains(., 'My Account')]") )
            )
        except TimeoutException:
            print("hover_open_booked_ticket_history: 'My Account' not found")
            return False

    try:
        # Hover over My Account to reveal submenu
        actions.move_to_element(my_account).pause(0.3).perform()
        time.sleep(0.4)
    except Exception:
        # If move_to_element fails, try clicking to open menu
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", my_account)
            driver.execute_script("arguments[0].click();", my_account)
            time.sleep(0.4)
        except Exception:
            pass

    # Now locate 'My Transactions' in revealed submenu
    try:
        my_txn = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[normalize-space()='My Transactions' or contains(normalize-space(.),'My Transactions') or contains(., 'My Transactions')]")
            )
        )
    except TimeoutException:
        # Try looser match (case-insensitive)
        try:
            my_txn = wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'my transactions')]") )
            )
        except TimeoutException:
            print("hover_open_booked_ticket_history: 'My Transactions' not found")
            return False

    try:
        # Hover over My Transactions to reveal nested submenu
        actions.move_to_element(my_txn).pause(0.3).perform()
        time.sleep(0.4)
    except Exception:
        # fallback to click
        try:
            driver.execute_script("arguments[0].click();", my_txn)
            time.sleep(0.4)
        except Exception:
            pass

    # Finally click 'Booked Ticket History'
    try:
        booked = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='Booked Ticket History' or contains(normalize-space(.),'Booked Ticket History') or contains(., 'Booked Ticket History')]")
            )
        )
        # ensure visible and click
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", booked)
        driver.execute_script("arguments[0].click();", booked)
        time.sleep(0.6)
        print("hover_open_booked_ticket_history: Clicked 'Booked Ticket History'")
        return True
    except TimeoutException:
        print("hover_open_booked_ticket_history: 'Booked Ticket History' not found")
        return False
    except Exception as e:
        print('hover_open_booked_ticket_history: error clicking Booked Ticket History ->', e)
        return False