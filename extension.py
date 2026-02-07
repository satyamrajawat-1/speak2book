# extension.py
import json
import os
import time

GLOBAL_JSON_FILE = "chatbot_data.json"

def load_global_json():
    """Load global JSON from file or create default"""
    default_json = {
        "current_intent": None,
        "slots": {
            "from_city": None,
            "to_city": None,
            "journey_date": None,
            "pnr": None,
            "train_no": None,
            "class": None,
            "quota": None,
            "passenger_index": None,
            "passenger_name": None,
            "passenger_age": None,
            "passenger_gender": None,
            "berth_preference": None
        },
        "passengers": [],
        "missing_slots": [],
        "next_action": None,
        "conversation_history": []
    }
    
    if os.path.exists(GLOBAL_JSON_FILE):
        try:
            with open(GLOBAL_JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return default_json
    
    return default_json

def save_global_json(data):
    """Save global JSON to file"""
    try:
        with open(GLOBAL_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"JSON saved to {GLOBAL_JSON_FILE}")
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False

def update_global_json(user_input, result):
    """Update global JSON with new conversation data"""
    global_data = load_global_json()
    
    # Add to conversation history
    if user_input:
        global_data.setdefault("conversation_history", []).append({
            "user": user_input,
            "response": result,
            "timestamp": time.time()
        })
    
    if isinstance(result, dict):
        # --- Trigger logic ---
        if result.get("trigger") == True:
            # Reset everything
            for key in global_data.get("slots", {}):
                global_data["slots"][key] = None
            global_data["passengers"] = []
            global_data["current_intent"] = result.get("intent")
            global_data["missing_slots"] = result.get("missing_slots", [])
            global_data["next_action"] = result.get("next_action")
        else:
            # --- Trigger is False ---
            # Update intent ONLY if current intent is None
            if global_data.get("current_intent") in [None, ""]:
                global_data["current_intent"] = result.get("intent", global_data.get("current_intent"))

        # --- Merge slots ---
        if "slots" in result:
            for key, value in result["slots"].items():
                # Only overwrite if value is not None or empty
                if value not in [None, ""]:
                    global_data["slots"][key] = value
                # If value is None or missing, keep existing slot as is

        # --- Merge passengers ---
        if "passengers" in result and result["passengers"]:
            for new_passenger in result["passengers"]:
                found = False
                for i, existing in enumerate(global_data.get("passengers", [])):
                    if existing.get("index") == new_passenger.get("index"):
                        global_data["passengers"][i].update(new_passenger)
                        found = True
                        break
                if not found:
                    global_data.setdefault("passengers", []).append(new_passenger)

        # --- Update missing slots and next action ---
        if "missing_slots" in result:
            global_data["missing_slots"] = result["missing_slots"]
        if "next_action" in result:
            global_data["next_action"] = result["next_action"]

    # Save updated JSON
    save_global_json(global_data)
    return global_data

def inject_chatbot(driver):
    """Inject chatbot with working JavaScript (very small, left bottom)"""
    script = """
    // Remove existing chatbot if present
    let oldDiv = document.getElementById('selenium-chatbot');
    if (oldDiv) oldDiv.remove();

    // Create new chatbot
    let div = document.createElement('div');
    div.id = 'selenium-chatbot';
    div.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        width: 280px;           /* HALF SIZE: 140px instead of 280px */
        background: white;
        border: 2px solid #007bff;
        z-index: 2147483647;
        padding: 6px;           /* Less padding */
        font-family: Arial, sans-serif;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        max-height: 320px;      /* Reduced height */
    `;

    div.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #eee;">
            <b style="color: #007bff; font-size: 10px;">🚂 Assistant</b>
            <button style="background: none; border: none; cursor: pointer; font-size: 14px; color: #666; padding: 0 2px;" 
                    onclick="document.getElementById('selenium-chatbot').style.display='none'">×</button>
        </div>
        
        <div id="chat-msgs" style="height: 80px; overflow-y: auto; padding: 4px; border: 1px solid #ddd; border-radius: 3px; margin-bottom: 6px; font-size: 10px; background: #fafafa;">
        </div>

        <div style="display: flex; gap: 3px; margin-bottom: 4px;">
            <input id="chat-input" type="text" style="flex: 1; padding: 4px; border: 1px solid #ccc; border-radius: 2px; font-size: 10px;" 
                   placeholder="Message..." autocomplete="off">
            <button onclick="startVoice()" style="padding: 4px 6px; background: #28a745; color: white; border: none; border-radius: 2px; cursor: pointer; font-size: 10px;">🎤</button>
            <button onclick="sendMessage()" style="padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 2px; cursor: pointer; font-size: 10px;">→</button>
        </div>
        
        <div id="status" style="font-size: 8px; color: #666; height: 12px; margin-top: 3px;"></div>
    `;

    document.body.appendChild(div);

    // Initialize message queue
    window.chatbot_message_queue = [];
    
    // Send message function
    window.sendMessage = function() {
        let inp = document.getElementById('chat-input');
        let msg = inp.value.trim();
        if (!msg) return;

        let box = document.getElementById('chat-msgs');
        box.innerHTML += '<div style="margin: 2px 0; padding: 3px; background: #e3f2fd; border-radius: 2px; font-size: 9px; word-wrap: break-word;">' +
                         '<b style="color:#007bff">You:</b> ' + msg.substring(0, 30) + (msg.length > 30 ? '...' : '') + '</div>';
        inp.value = '';
        
        window.chatbot_message_queue.push(msg);
        document.getElementById('status').textContent = 'Processing...';
        box.scrollTop = box.scrollHeight;
        
        // Clear status after 2 seconds
        setTimeout(() => {
            document.getElementById('status').textContent = '';
        }, 2000);
    }

    // Voice function
    window.startVoice = function() {
        if (!window.webkitSpeechRecognition && !window.SpeechRecognition) {
            document.getElementById('status').textContent = 'No voice';
            return;
        }

        let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let rec = new SpeechRecognition();
        rec.lang = "en-US";
        rec.continuous = false;
        rec.interimResults = false;
        
        document.getElementById('status').textContent = '🎤...';
        document.getElementById('chat-input').placeholder = "Listening";

        rec.onresult = function(e) {
            let transcript = e.results[0][0].transcript;
            document.getElementById('chat-input').value = transcript;
            document.getElementById('status').textContent = 'Heard...';
            sendMessage();
        };
        
        rec.onerror = function(e) {
            document.getElementById('status').textContent = 'Error';
            document.getElementById('chat-input').placeholder = "Message...";
        };
        
        rec.onend = function() {
            document.getElementById('chat-input').placeholder = "Message...";
            setTimeout(() => {
                document.getElementById('status').textContent = '';
            }, 3000);
        };

        rec.start();
    }

    // Enter key support
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Focus input on load
    setTimeout(() => {
        document.getElementById('chat-input').focus();
    }, 300);
    """

    driver.execute_script(script)