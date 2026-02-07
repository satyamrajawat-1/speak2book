import time
import json
from datetime import datetime
import undetected_chromedriver as uc
from extension import load_global_json, update_global_json, inject_chatbot, GLOBAL_JSON_FILE
from text_to_json import get_irctc_json
from irctc import handle_aadhaar_popup, set_station, select_class, select_date, click_search_trains
from validation import update_irctc_form,checker

def escape_for_js(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
    return text

# --- Main ---
def main():
    print("🚂 Starting IRCTC + Chatbot automation...")
    
    # --- Start IRCTC browser ---
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(version_main=144, options=options)
    driver.get("https://www.irctc.co.in")
    time.sleep(5)

    handle_aadhaar_popup(driver)  # remove popup

    # Inject chatbot on same page
    inject_chatbot(driver)
    driver.execute_script("""
        let box = document.getElementById('chat-msgs');
        box.innerHTML = '<div style="padding:8px; background:#e3f2fd; border-radius:5px; margin:5px 0;">' +
                        '<b style="color:#007bff">🤖 Assistant:</b> Ready to take your commands!</div>';
    """)

    print("✅ Chatbot ready on IRCTC page. Type messages now.")

    try:
        while True:
            # Get new messages from chat
            messages = driver.execute_script("""
                if(window.chatbot_message_queue && window.chatbot_message_queue.length > 0){
                    let msgs = window.chatbot_message_queue;
                    window.chatbot_message_queue = [];
                    return msgs;
                }
                return [];
            """)

            for msg in messages:
                # Convert to JSON
                result = get_irctc_json(msg)
                update_global_json(msg, result)
                print(f"📝 Saved JSON intent:")
                print(json.dumps(result, indent=2))

                # Fill IRCTC form dynamically
                checker(driver)

                # Display chatbot response
                display_text = f"🎯 Intent: {result.get('intent')}"
                driver.execute_script(f"""
                    let box = document.getElementById('chat-msgs');
                    if(box){{
                        box.innerHTML += '<div style="margin:6px 0; padding:8px; background:#f0fff0; border-radius:5px;">' +
                                         '<b style="color:#28a745">🤖 Bot:</b> ' + {json.dumps(display_text)} + '</div>';
                        box.scrollTop = box.scrollHeight;
                    }}
                """)

            time.sleep(0.3)

    except KeyboardInterrupt:
        print("🛑 Keyboard interrupt. Exiting.")
    finally:
        print("💾 Automation stopped. IRCTC browser remains open for review.")

if __name__ == "__main__":
    main()
