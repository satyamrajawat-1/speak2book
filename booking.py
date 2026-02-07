import time
import datetime
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


# ---------------- CHATBOT INJECTION ----------------
def inject_chatbot(driver):
    """Inject minimal voice-enabled chatbot into the page"""
    script = """
    // Create chatbot
    let div = document.getElementById('selenium-chatbot');
    if (!div) {
        div = document.createElement('div');
        div.id = 'selenium-chatbot';
        div.style = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            width: 250px;
            background: white;
            border: 2px solid #000;
            z-index: 999999;
            padding: 5px;
            font: 12px Arial;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            border-radius: 5px;
        `;
        div.innerHTML = `
            <div style="background:#000;color:white;padding:2px 5px;border-radius:3px;">
                <b>🤖 IRCTC Assistant</b> 
                <button style="float:right;background:none;border:none;color:white;cursor:pointer" onclick="this.parentNode.parentNode.style.display='none'">X</button>
            </div>
            <div id="chat-msgs" style="height:100px;overflow:auto;margin:5px 0;border:1px solid #ccc;padding:2px;background:#f9f9f9;"></div>
            <div style="display:flex;gap:2px;">
                <input id="chat-input" style="flex:1;padding:4px;border:1px solid #ccc;" placeholder="Type command...">
                <button onclick="chatSend()" style="padding:4px 8px;background:#4CAF50;color:white;border:none;cursor:pointer">▶</button>
                <button onclick="chatVoice()" title="Voice" style="padding:4px 8px;background:#2196F3;color:white;border:none;cursor:pointer">🎤</button>
            </div>
        `;
        document.body.appendChild(div);
        
        
        function resetHideTimer() {
            clearTimeout(hideTimer);
            hideTimer = setTimeout(() => div.style.display = 'none', 30000);
        }
        
        // Add hover to show
        div.addEventListener('mouseenter', () => clearTimeout(hideTimer));
        div.addEventListener('mouseleave', () => hideTimer = setTimeout(() => div.style.display = 'none', 30000));
        
        function chatSend() {
            resetHideTimer();
            let inp = document.getElementById('chat-input');
            let msg = inp.value.trim();
            if (!msg) return;
            
            addMessage('You: ' + msg);
            inp.value = '';
            
            // Process commands
            let resp = processCommand(msg.toLowerCase());
            addMessage('Bot: ' + resp);
            
            // Speak response
            if (window.speechSynthesis) {
                let speech = new SpeechSynthesisUtterance(resp);
                speech.rate = 1.0;
                speechSynthesis.speak(speech);
            }
        }
        
        function processCommand(cmd) {
            // IRCTC-specific commands
            if (cmd.includes('help')) return 'Commands: url, title, status, scroll top/bottom, elements, click first, find [text]';
            if (cmd.includes('url')) return 'Current URL: ' + window.location.href;
            if (cmd.includes('title')) return 'Page title: ' + document.title;
            if (cmd.includes('status')) return 'Page loaded. Elements found: ' + document.querySelectorAll('*').length;
            
            if (cmd.includes('scroll top')) {
                window.scrollTo(0, 0);
                return 'Scrolled to top';
            }
            if (cmd.includes('scroll bottom')) {
                window.scrollTo(0, document.body.scrollHeight);
                return 'Scrolled to bottom';
            }
            
            if (cmd.includes('elements')) {
                let buttons = document.querySelectorAll('button').length;
                let inputs = document.querySelectorAll('input').length;
                let links = document.querySelectorAll('a').length;
                return `Elements: ${buttons} buttons, ${inputs} inputs, ${links} links`;
            }
            
            if (cmd.includes('click first')) {
                let btn = document.querySelector('button');
                if (btn) {
                    btn.click();
                    return 'Clicked first button';
                }
                return 'No buttons found';
            }
            
            if (cmd.includes('find ')) {
                let search = cmd.split('find ')[1];
                if (search) {
                    let elements = document.querySelectorAll('*');
                    for (let el of elements) {
                        if (el.textContent && el.textContent.includes(search)) {
                            el.scrollIntoView({behavior: 'smooth'});
                            return `Found "${search}" in element`;
                        }
                    }
                    return `"${search}" not found`;
                }
            }
            
            // IRCTC page detection
            if (window.location.href.includes('irctc')) {
                if (document.title.includes('Login')) return 'You are on IRCTC login page';
                if (document.title.includes('Book Ticket')) return 'You are on booking page';
                if (document.querySelector('input[placeholder*="Name"]')) return 'Passenger details page';
            }
            
            return 'Command: ' + cmd;
        }
        
        function chatVoice() {
            resetHideTimer();
            if (window.webkitSpeechRecognition || window.SpeechRecognition) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-US';
                recognition.interimResults = false;
                
                recognition.onresult = (e) => {
                    let transcript = e.results[0][0].transcript;
                    document.getElementById('chat-input').value = transcript;
                    chatSend();
                };
                
                recognition.onerror = (e) => {
                    addMessage('Bot: Voice error: ' + e.error);
                };
                
                recognition.start();
                addMessage('Bot: Listening...');
            } else {
                addMessage('Bot: Voice not supported');
            }
        }
        
        function addMessage(text) {
            let msgs = document.getElementById('chat-msgs');
            let msgDiv = document.createElement('div');
            msgDiv.textContent = text;
            msgDiv.style.padding = '2px 0';
            msgs.appendChild(msgDiv);
            msgs.scrollTop = msgs.scrollHeight;
        }
        
        window.chatSend = chatSend;
        window.chatVoice = chatVoice;
        
        // Initial message
        addMessage('Bot: IRCTC Assistant ready. Say "help" for commands.');
    }
    """
    try:
        driver.execute_script(script)
        print("🤖 Chatbot injected")
    except Exception as e:
        print(f"Failed to inject chatbot: {e}")


# ---------------- NAVIGATE AND INJECT ----------------
def navigate_and_inject(driver, url):
    """Navigate to URL and inject chatbot"""
    driver.get(url)
    time.sleep(3)
    inject_chatbot(driver)
    return True


# ---------------- Aadhaar Popup ----------------
def handle_aadhaar_popup(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='OK']"))
        ).click()
        print("Aadhaar alert popup accepted.")
        time.sleep(1)
        inject_chatbot(driver)  # Re-inject after popup
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
    inject_chatbot(driver)  # Re-inject after navigation

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
    inject_chatbot(driver)  # Re-inject after login


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
    inject_chatbot(driver)  # Re-inject after search results


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
    time.sleep(3)
    inject_chatbot(driver)  # Re-inject after booking page


# ---------------- Passenger Details & Contact ----------------

def confirm_food_dialog(driver, timeout=6):
    """Wait for the Confirmation dialog about food/beverages and click OK."""
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

    # 2) Generic dialog containers
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
    """Fill passenger names, age, gender, berth preference and contact number, then click Continue."""
    wait = WebDriverWait(driver, timeout)

    # wait for passenger name inputs to appear
    try:
        name_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[placeholder='Name']")))
    except TimeoutException:
        print("Passenger form not found.")
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

    # try to unselect food/beverages
    try:
        # search for a label containing 'food' or 'beverage'
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
        
        time.sleep(5)
        inject_chatbot(driver)  # Inject on payment page
        
        print("🤖 Chatbot active! You can use voice/text commands.")
        print("Commands: 'help', 'url', 'title', 'status', 'scroll top', 'find [text]'")
        
        if KEEP_BROWSER_OPEN:
            print("Browser will stay open for manual payment/inspection.")
            print("Press Ctrl+C in terminal to exit script (browser will remain).")
            
            # Keep script running to maintain chatbot
            try:
                while True:
                    time.sleep(1)
                    # Check for page navigation and re-inject
                    current_url = driver.current_url
                    if hasattr(driver, '_last_url') and driver._last_url != current_url:
                        inject_chatbot(driver)
                        driver._last_url = current_url
            except KeyboardInterrupt:
                print("\nScript stopped by user. Browser remains open.")
        else:
            input("Press ENTER to close the script and browser...")
            return

    except Exception as e:
        print("Failed to click Continue:", e)


# ===================== MAIN =====================
# Set to True to KEEP the browser open after navigating to review/payment
KEEP_BROWSER_OPEN = True

driver = None
try:
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    # Enable voice permissions
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = uc.Chrome(version_main=144, options=options)
    
    # Initial navigation with chatbot injection
    navigate_and_inject(driver, "https://www.irctc.co.in")
    driver._last_url = driver.current_url  # Track URL for re-injection
    
    handle_aadhaar_popup(driver)
    login_irctc(driver, "Satyam_rajawat113", "Satyam@28312")

    set_station(driver, "Kota", "From")
    set_station(driver, "NDLS", "To")

    select_class(driver, "AC 2 Tier (2A)")
    select_date(driver, "05/03/2026")
    click_search_trains(driver)

    select_class_and_book(
        driver,
        train_number="12951",
        class_name="AC 2 Tier (2A)"
    )

    # --- Passenger data: edit as needed ---
    PASSENGERS = [
        {"name": "Raghav Gupta", "age": 28, "gender": "M", "berth": "LB"},
        {"name": "Pankaj Gupta", "age": 50, "gender": "M", "berth": "UB"},
    ]
    MOBILE_NUMBER = "9200000075"  # edit to your contact number (10 digits)

    # fill passenger details and continue to review/payment
    fill_passenger_details(driver, PASSENGERS, MOBILE_NUMBER)

    # Keep the browser open if flag is set
    if KEEP_BROWSER_OPEN:
        print("🤖 Chatbot remains active. You can interact with it.")
        print("The chatbot auto-hides after 30s inactivity. Hover to show.")
        print("Close browser manually when done.")

except Exception as e:
    print(f"Error in main execution: {e}")
    import traceback
    traceback.print_exc()

finally:
    if driver and not KEEP_BROWSER_OPEN:
        driver.quit()