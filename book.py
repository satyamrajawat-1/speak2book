import time
import datetime
import base64
import os
import tempfile
import webbrowser
import urllib.request
import cv2
import pytesseract
import os


from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
#-----------------Extra Functions---------------------------
import os
import cv2
import pytesseract

def extract_text_from_image(image_path):
    # Set tesseract path (Windows only)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if not os.path.exists(image_path):
        return ""

    img = cv2.imread(image_path)
    if img is None:
        return ""

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply threshold to improve text clarity
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # Extract text
    text = pytesseract.image_to_string(gray, config="--psm 6")

    return text.strip()


# ---------------- Station Selector ----------------
def set_station(driver, station_name, field="From", timeout=10):
    wait = WebDriverWait(driver, timeout)
    aria = f"Enter {field} station. Input is Mandatory."

    input_box = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"input[aria-label='{aria}']"))
    )
    input_box.clear()
    input_box.send_keys(station_name)
    time.sleep(1)

    for _ in range(6):
        try:
            items = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "li.ui-autocomplete-list-item")
                )
            )
            for li in items:
                if li.text.strip() and "-----" not in li.text:
                    driver.execute_script("arguments[0].click();", li)
                    print(f"'{field}' station set to: {li.text.strip()}")
                    return
        except StaleElementReferenceException:
            time.sleep(0.3)

    raise Exception(f"Failed to set {field} station")


# ---------------- Class Selector ----------------
def select_class(driver, class_name):
    wait = WebDriverWait(driver, 10)

    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "span.ui-dropdown-label"))
    ).click()
    time.sleep(0.6)

    items = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "li.ui-dropdown-item")
        )
    )

    for li in items:
        if li.text.strip() == class_name:
            driver.execute_script("arguments[0].click();", li)
            print(f"Class selected: {class_name}")
            return

    raise Exception("Class not found")


# ---------------- Date Selector ----------------
def select_date(driver, dateInput):
    wait = WebDriverWait(driver, 10)
    target_date = datetime.datetime.strptime(dateInput, "%d/%m/%Y")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//p-calendar//input"))
    ).click()
    time.sleep(0.6)

    while True:
        month = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-datepicker-month"))
        ).text
        year = driver.find_element(By.CLASS_NAME, "ui-datepicker-year").text

        if month == target_date.strftime("%B") and year == str(target_date.year):
            break

        driver.find_element(By.CLASS_NAME, "ui-datepicker-next").click()
        time.sleep(0.4)

    day = str(target_date.day)
    driver.find_element(
        By.XPATH, f"//a[text()='{day}' and not(contains(@class,'ui-state-disabled'))]"
    ).click()

    print(f"Journey date selected: {dateInput}")


# ---------------- Search Button ----------------
def click_search_trains(driver):
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Search')]"))
    ).click()
    print("✅ Search button clicked successfully.")
    time.sleep(3)


# ---------------- Book Train by Number (VISIBLE SCROLL) ----------------
def select_class_and_book(driver, train_number, class_name, timeout=30):
    wait = WebDriverWait(driver, timeout)

    # 1️⃣ Locate the train card
    train_card = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//app-train-avl-enq[.//strong[contains(text(),'({train_number})')]]"
        ))
    )

    # 2️⃣ Click class from FIRST class table (pre-avl)
    class_button = train_card.find_element(
        By.XPATH,
        f".//div[contains(@class,'pre-avl')]//strong[normalize-space()='{class_name}']"
    )

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", class_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", class_button)

    print(f"Class clicked: {class_name}")

    # 3️⃣ Wait for availability grid to load
    available_cell = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            ".//div[contains(@class,'AVAILABLE') and .//strong[contains(text(),'AVAILABLE')]]"
        ))
    )

    driver.execute_script("arguments[0].click();", available_cell)
    print("AVAILABLE date selected")
    time.sleep(1)

    # 4️⃣ Wait until Book Now becomes enabled
    book_now_btn = train_card.find_element(
        By.XPATH, ".//button[normalize-space()='Book Now']"
    )

    wait.until(
        lambda d: "disable-book" not in book_now_btn.get_attribute("class")
    )

    # 5️⃣ Click Book Now
    driver.execute_script("arguments[0].click();", book_now_btn)
    print("✅ Book Now clicked successfully")
    time.sleep(1)
    
    # 6️⃣ Handle any confirmation dialog that appears
    handle_book_now_confirmation(driver, timeout=8)


# ---------------- Passenger Details & Contact ----------------

def handle_book_now_confirmation(driver, timeout=8):
    """Handle any confirmation popup/dialog that appears after clicking Book Now.
    Looks for Yes/OK buttons and clicks them.
    Returns True if successfully handled, False otherwise."""
    wait = WebDriverWait(driver, timeout)

    # 1) Try PrimeNG confirm dialog with Yes button
    precise_xpaths = [
        "//div[contains(@class,'ui-dialog') and .//span[contains(., 'Yes')]]//button[.//span[contains(., 'Yes')]]",
        "//p-confirmdialog//button[contains(., 'Yes')]",
        "//div[contains(@class,'ui-dialog')]//button[contains(., 'Yes')]",
        "//button[normalize-space()='Yes']",
    ]
    
    for xp in precise_xpaths:
        try:
            yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].click();", yes_btn)
            print("Clicked Yes on Book Now confirmation dialog.")
            time.sleep(0.5)
            return True
        except TimeoutException:
            continue

    # 2) Try OK button as fallback
    ok_xpaths = [
        "//div[contains(@class,'ui-dialog')]//button[normalize-space()='OK']",
        "//button[normalize-space()='OK']",
        "//button[contains(., 'OK')]",
    ]
    
    for xp in ok_xpaths:
        try:
            ok_btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].click();", ok_btn)
            print("Clicked OK on Book Now confirmation dialog.")
            time.sleep(0.5)
            return True
        except TimeoutException:
            continue

    return False


def confirm_food_dialog(driver, timeout=6):
    """Wait for the Confirmation dialog about food/beverages and click OK.
    Uses a precise selector for the IRCTC confirmation modal (see yep2.html), then falls back to generic strategies.
    Returns True if OK was clicked, False otherwise."""
    wait = WebDriverWait(driver, timeout)

    # 1) Precise selector matching the structure in `yep2.html` (Confirmation dialog inside a ui-dialog)
    precise_xpath = "//div[contains(@class,'ui-dialog') and .//span[normalize-space()='Confirmation']]//button[.//span[normalize-space()='OK']]"
    try:
        ok_btn = wait.until(EC.element_to_be_clickable((By.XPATH, precise_xpath)))
        driver.execute_script("arguments[0].click();", ok_btn)
        print("Clicked OK on confirmation dialog (precise selector).")
        return True
    except TimeoutException:
        pass

    # 2) Generic dialog containers that likely contain the message (case-insensitive search for 'food')
    dialog_xpaths = [
        "//div[contains(@class,'modal') and .//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'food')]]",
        "//div[contains(@role,'dialog') and .//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'food')]]",
        "//div[.//h4[normalize-space()='Confirmation'] or .//strong[normalize-space()='Confirmation'] or .//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'food/beverages')]]",
        "//p-confirmdialog//div[contains(@class,'ui-dialog')]",
    ]

    ok_xpaths = [
        ".//button[normalize-space()='OK']",
        ".//button[normalize-space()='Ok']",
        ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'ok')]",
        ".//a[normalize-space()='OK']",
        ".//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'ok')]",
        ".//input[@type='button' and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'ok')]",
    ]

    for dx in dialog_xpaths:
        try:
            dialog = wait.until(EC.presence_of_element_located((By.XPATH, dx)))
            for ox in ok_xpaths:
                try:
                    ok_btn = dialog.find_element(By.XPATH, ox)
                    if ok_btn and ok_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", ok_btn)
                        print("Clicked OK on confirmation dialog (dialog-scoped fallback).")
                        return True
                except Exception:
                    continue
        except TimeoutException:
            continue

    # 3) Last-resort: scan entire page for OK/Yes buttons
    page_level = [
        "//button[normalize-space()='OK']",
        "//button[normalize-space()='Ok']",
        "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
        "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'yes')]",
        "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
    ]
    for xp in page_level:
        try:
            ok_btn = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].click();", ok_btn)
            print(f"Clicked OK using page-level fallback: {xp}")
            return True
        except Exception:
            continue

    return False


def fill_passenger_details(driver, passengers, mobile, timeout=10):
    """Fill passenger names, age, gender, berth preference and contact number, then click Continue.
    Automatically adds more passengers by clicking the 'Add Passenger' button as needed."""
    wait = WebDriverWait(driver, timeout)

    # wait for passenger name inputs to appear
    try:
        name_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[placeholder='Name']")))
    except TimeoutException:
        print("Passenger form not found.")
        return

    # Add more passenger forms if needed
    num_passengers = len(passengers)
    current_form_count = len(driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Name']"))
    
    print(f"Total passengers to add: {num_passengers}, Current forms available: {current_form_count}")
    
    # Click "Add Passenger" button to add more forms
    if current_form_count < num_passengers:
        passengers_to_add = num_passengers - current_form_count
        for i in range(passengers_to_add):
            try:
                # Find and click the "Add Passenger" link
                add_passenger_link = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Add Passenger') or contains(., 'add passenger')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_passenger_link)
                driver.execute_script("arguments[0].click();", add_passenger_link)
                print(f"Clicked 'Add Passenger' button (iteration {i+1}/{passengers_to_add})")
                time.sleep(0.8)  # Wait for new form to load
            except Exception as e:
                print(f"Failed to click 'Add Passenger' button on iteration {i+1}: {e}")
                break

    # Re-fetch all form elements after adding passengers
    try:
        name_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[placeholder='Name']")))
    except TimeoutException:
        print("Passenger forms not found after adding passengers.")
        return

    age_inputs = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Age'], input[formcontrolname='passengerAge']")
    gender_selects = driver.find_elements(By.CSS_SELECTOR, "select[formcontrolname='passengerGender']")
    berth_selects = driver.find_elements(By.CSS_SELECTOR, "select[formcontrolname='passengerBerthChoice']")

    for i, p in enumerate(passengers):
        if i < len(name_inputs):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", name_inputs[i])
            name_inputs[i].clear()
            name_inputs[i].send_keys(p.get('name',''))
            time.sleep(0.2)

        if i < len(age_inputs) and p.get('age') is not None:
            age_inputs[i].clear()
            age_inputs[i].send_keys(str(p['age']))
            time.sleep(0.1)

        if i < len(gender_selects) and p.get('gender'):
            sel = gender_selects[i]
            val = p['gender']
            # try to set by value (M/F/T) or by visible text
            set_done = False
            for opt in sel.find_elements(By.TAG_NAME, 'option'):
                if opt.get_attribute('value') == val or opt.text.strip().lower().startswith(val.lower()):
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))", sel, opt.get_attribute('value'))
                    time.sleep(0.1)
                    set_done = True
                    break
            if not set_done:
                print(f"Could not set gender for passenger {i} -> {p}")

        if i < len(berth_selects) and p.get('berth'):
            sel = berth_selects[i]
            val = p['berth']
            for opt in sel.find_elements(By.TAG_NAME, 'option'):
                if opt.get_attribute('value') == val or opt.text.strip().lower().startswith(val.lower()):
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))", sel, opt.get_attribute('value'))
                    time.sleep(0.1)
                    break

    # fill mobile number
    try:
        mobile_input = driver.find_element(By.ID, "mobileNumber")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", mobile_input)
        mobile_input.clear()
        mobile_input.send_keys(mobile)
        print("Mobile number filled.")
    except Exception as e:
        print("Mobile input not found:", e)

    # try to unselect food/beverages (check 'I don't want food and beverages') and accept confirmation
    try:
        # search for a label containing 'food' or 'beverage' (case-insensitive)
        label = None
        xpaths = [
            "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'food') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'beverage') ]",
            "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"don't\") and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'food')]",
            "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i do not want') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'food')]"
        ]
        for xp in xpaths:
            elems = driver.find_elements(By.XPATH, xp)
            if elems:
                label = elems[0]
                break

        if label:
            checkbox = None
            try:
                checkbox = label.find_element(By.XPATH, ".//input[@type='checkbox']")
            except Exception:
                try:
                    checkbox = label.find_element(By.XPATH, "preceding::input[@type='checkbox'][1]")
                except Exception:
                    cands = driver.find_elements(By.XPATH, "//input[@type='checkbox' and (following::label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'food') ] or preceding::label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'food') ])]")
                    if cands:
                        checkbox = cands[0]

            if checkbox:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    print("No-food checkbox clicked. Waiting for confirmation dialog...")
                    try:
                        # first try the targeted dialog handler
                        confirmed = confirm_food_dialog(driver, timeout=6)
                        if confirmed:
                            print("No-food confirmation handled by modal OK click.")
                        else:
                            # fallback to scanning for any OK/Yes button on page
                            ok_global = [
                                "//button[normalize-space()='OK']",
                                "//button[normalize-space()='Ok']",
                                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'yes')]",
                                "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                                "//input[@type='button' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                            ]
                            clicked = False
                            for xp in ok_global:
                                try:
                                    ok_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xp)))
                                    driver.execute_script("arguments[0].click();", ok_btn)
                                    print(f"Confirmed no-food dialog by clicking global element matching: {xp}")
                                    clicked = True
                                    time.sleep(0.5)
                                    break
                                except TimeoutException:
                                    continue

                            if not clicked:
                                try:
                                    active = driver.switch_to.active_element
                                    active.send_keys(Keys.ENTER)
                                    print("Pressed ENTER as fallback to confirm dialog.")
                                    time.sleep(0.5)
                                    clicked = True
                                except Exception:
                                    print("Confirmation dialog OK not found, checkbox clicked but not confirmed.")
                    except Exception as e:
                        print("Error while trying to confirm dialog:", e)
                else:
                    print("No-food checkbox already selected.")

            else:
                print("No-food checkbox not found near label.")
        else:
            print("No label for food option found.")
    except Exception as e:
        print("Error when trying to disable food option:", e)

    # ensure BHIM/UPI payment is selected
    try:
        upi_radio = None
        # try to find radio with value '2' (BHIM/UPI) or labels containing 'bhim'/'upi'
        radios = driver.find_elements(By.XPATH, "//input[@name='paymentType' and (@value='2' or contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'upi'))]")
        if radios:
            upi_radio = radios[0]
        else:
            labs = driver.find_elements(By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bhim') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upi')]")
            if labs:
                try:
                    upi_radio = labs[0].find_element(By.XPATH, ".//input[@type='radio']")
                except Exception:
                    pass

        if upi_radio:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", upi_radio)
            if not upi_radio.is_selected():
                driver.execute_script("arguments[0].click();", upi_radio)
                print("Selected BHIM/UPI payment option.")
            else:
                print("BHIM/UPI already selected.")
        else:
            print("BHIM/UPI radio not found.")
    except Exception as e:
        print("Error selecting BHIM/UPI:", e)

    # click Continue
    try:
        continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.train_Search.btnDefault, button[type=submit]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", continue_btn)
        driver.execute_script("arguments[0].click();", continue_btn)
        print("Continue clicked — moving to review/payment page.")
    except Exception as e:
        print("Failed to click Continue:", e)


def handle_captcha_and_continue(driver, timeout=120):
    """Save captcha image, open it for the user, prompt for text, fill captcha and click Continue."""
    wait = WebDriverWait(driver, timeout)
    try:
        img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.captcha-img")))
        src = img.get_attribute('src')
    except TimeoutException:
        print("Captcha image not found on review page.")
        return False

    # Save captcha to temporary file
    try:
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        if src and src.startswith('data:image'):
            header, b64 = src.split(',', 1)
            data = base64.b64decode(b64)
            with open(path, 'wb') as f:
                f.write(data)
        else:
            # fallback: try to download via urllib
            try:
                urllib.request.urlretrieve(src, path)
            except Exception as e:
                print('Failed to save captcha image:', e)
                return False

        # Open image for user to read (Windows: os.startfile)
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                webbrowser.open(path)
        except Exception:
            webbrowser.open(path)

        # Prompt user to enter captcha
        #Manual Captcha
        #captcha_value = input('Please enter captcha shown in opened image: ').strip()
        #By function method
        captcha_value = extract_text_from_image(path)
        if not captcha_value:
            print('No captcha entered, aborting.')
            return False

        # Fill captcha input and click Continue
        try:
            captcha_input = wait.until(EC.presence_of_element_located((By.ID, 'captcha')))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", captcha_input)
            captcha_input.clear()
            captcha_input.send_keys(captcha_value)
            time.sleep(0.3)

            # find Continue button (desktop/mobile variants)
            try:
                continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.train_Search, button[type=submit], button.btnDefault.train_Search")))
            except Exception:
                # last resort: find button with text Continue
                continue_btn = driver.find_element(By.XPATH, "//button[contains(normalize-space(.),'Continue') or contains(normalize-space(.),'CONTINUE')]")

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", continue_btn)
            driver.execute_script("arguments[0].click();", continue_btn)
            print('Captcha entered and Continue clicked.')
            return True
        except Exception as e:
            print('Failed to enter captcha or click Continue:', e)
            return False
    finally:
        # optional: keep the captcha file for inspection; do not delete immediately
        pass


def handle_payment_selection(driver, timeout=30):
    """Select BHIM/UPI/USSD payment option and click the BHIM/Paytm pay button (with fallbacks)."""
    wait = WebDriverWait(driver, timeout)
    try:
        # wait for payment options area (many IRCTC pages use id 'pay-type')
        wait.until(EC.presence_of_element_located((By.ID, 'pay-type')))
    except Exception:
        # fallback: wait for any bank-type tile
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'bank-type')]")))
        except Exception:
            print('Payment options area not found.')
            return False

    # Attempt to click the BHIM/UPI/USSD payment tile
    bhim_xpaths = [
        "//div[contains(@class,'bank-type') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bhim') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upi')]",
        "//div[contains(@class,'bank-type') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bhim')]",
        "//div[contains(normalize-space(.),'BHIM/ UPI/ USSD') or contains(normalize-space(.),'BHIM/ UPI/USSD')]",
    ]

    clicked = False
    for xp in bhim_xpaths:
        try:
            el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            print('Clicked BHIM/UPI/USSD payment option.')
            clicked = True
            time.sleep(0.6)
            break
        except Exception:
            continue

    if not clicked:
        print('Could not find BHIM/UPI/USSD payment tile; aborting payment selection.')
        return False

    # Wait for and click the Pay using BHIM (Paytm) button, with fallbacks
    pay_xpaths = [
        "//button[contains(normalize-space(.),'Pay using BHIM') or contains(normalize-space(.),'Pay using BHIM (Powered')]",
        "//a[contains(normalize-space(.),'Pay using BHIM') or contains(normalize-space(.),'Pay using BHIM (Powered')]",
        "//button[contains(normalize-space(.),'Pay & Book') or contains(normalize-space(.),'Pay & Book')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pay') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bhim')]",
    ]

    for xp in pay_xpaths:
        try:
            btn = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            driver.execute_script("arguments[0].click();", btn)
            print('Clicked pay button (xpath):', xp)
            return True
        except Exception:
            continue

    # Last resort: click any prominent 'Pay' or 'Pay & Book' button on page
    try:
        generic = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pay') and (contains(., '&') or contains(., 'Book'))]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", generic)
        driver.execute_script("arguments[0].click();", generic)
        print('Clicked generic Pay button.')
        return True
    except Exception:
        print('Failed to find a pay button for BHIM; please click it manually in the browser.')
        return False
