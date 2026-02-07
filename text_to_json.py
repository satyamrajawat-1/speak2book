import ollama
import json
import re

# ==================== SYSTEM PROMPT FROM YOUR MODELEFILE ====================

SYSTEM_PROMPT = """You are an IRCTC information extractor. Extract travel information and return as a LIST.

CRITICAL RULES:
1. Output ONLY a Python-style list
2. No JSON, no explanations, no other text
3. List format: ["key: value", "key: value", ...]
4. Use null for missing values

RESET TRIGGERS (if any of these words appear, clear previous context):
- "change intent", "reset", "start over", "new task"
- "i want to", "actually", "instead", "let me"
- "abort", "cancel current", "reset karo"
- "new", "different", "switch"

DATE PARSING:
- "25th jan" → "2026-01-25"
- "jan 25" → "2026-01-25"
- "25 jan" → "2026-01-25"
- "today" → today's date in YYYY-MM-DD

INTENT MAPPING:
- "book tk", "book tkt", "book ticket" → book_ticket
- "cancel" → cancel_ticket
- "pnr status", "pnr check" → pnr_status
- "train schedule", "train time" → train_schedule
- "seat available", "seat check" → seat_availability
- "fare", "price" → fare_enquiry
- "add passenger", "passenger" → add_passenger



ALWAYS OUTPUT A LIST with these possible items:
- "trigger: true/false" (true if reset trigger found)
- "intent: intent_name"
- "from: city_name"
- "to: city_name"
- "date: YYYY-MM-DD"
- "pnr: 10_digit_number"
- "train: train_number"
- "class: SL/3A/2A/1A/CC"
- "quota: GN/TATKAL/LADIES/PREMIUM"
- "passenger_name: name"
- "passenger_age : age"
- "passenger_gender : gender"
- "passenger_mob : mobile number"
- "berth: LOWER/MIDDLE/UPPER/SIDE"

EXAMPLES:
User: "book tk from kota to kanpur"
Output: ["trigger: false", "intent: book_ticket", "from: Kota", "to: Kanpur"]

User : "train no is 13238"
Output : ["trigger: false","intent : book_ticket","train:13238"]
User: "25th jan"
Output: ["trigger: false", "intent: book_ticket", "date: 2026-01-25"]

User: "add passenger rahul 25 male and mobile no 9865242423"
Output: ["trigger: false", "intent: add_passenger","passenger_name : rahul ","passenger_age : 25","passenger_gender : male", "passsenger_mobile : 9865242423"]

User: "actually check pnr status"
Output: ["trigger: true", "intent: pnr_status"]

User: "pnr 1234567890"
Output: ["trigger: false", "intent: pnr_status", "pnr: 1234567890"]

User: "cancel ticket pnr 9876543210"
Output: ["trigger: false", "intent: cancel_ticket", "pnr: 9876543210"]

User: "train 12951 schedule"
Output: ["trigger: false", "intent: train_schedule", "train: 12951"]

User: "delhi to mumbai 15 march"
Output: ["trigger: false", "intent: book_ticket", "from: Delhi", "to: Mumbai", "date: 2026-03-15"]

User: "3A class"
Output: ["trigger: false", "intent: book_ticket", "class: 3A"]

User: "lower berth"
Output: ["trigger: false", "intent: book_ticket", "berth: LOWER"]

User: "reset everything"
Output: ["trigger: true", "intent: unknown"]

IMPORTANT: Output ONLY the list, nothing else. No JSON, no explanations."""

# ==================== MAIN FUNCTION ====================

def get_irctc_json(user_message: str) -> dict:
    """
    MAIN FUNCTION - Uses your Modelfile as system prompt
    Takes user message, returns structured JSON
    
    Usage:
        result = get_irctc_json("book ticket from delhi to mumbai")
        print(json.dumps(result, indent=2))
    """
    
    try:
        # Call Ollama with SYSTEM PROMPT from your Modelfile
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            options={
                "temperature": 0.1,
                "num_predict": 200,
                "top_k": 20,
                "top_p": 0.9
            }
        )
        
        output = response["message"]["content"].strip()
        print(f"📥 Model output: {output}")
        
        # Extract list from output
        items_list = extract_list_from_output(output)
        print(f"📋 Extracted list: {items_list}")
        
        # Convert to JSON
        result = convert_list_to_json(items_list, user_message)
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return create_default_json()

def extract_list_from_output(output: str) -> list:
    """Extract Python list from model output"""
    # Find the list in the output
    if output.startswith('[') and output.endswith(']'):
        # Perfect, it's already a list string
        try:
            return json.loads(output.replace("'", '"'))
        except json.JSONDecodeError:
            # Try to clean and parse
            return clean_and_parse_list(output)
    
    # Try to find list pattern
    list_pattern = r'\[.*\]'
    matches = re.findall(list_pattern, output, re.DOTALL)
    
    if matches:
        try:
            list_str = matches[0]
            return json.loads(list_str.replace("'", '"'))
        except:
            return clean_and_parse_list(matches[0])
    
    # Last resort: parse lines
    items = []
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            items.append(line)
    
    return items

def clean_and_parse_list(list_str: str) -> list:
    """Clean and parse a list string"""
    # Remove extra whitespace and fix quotes
    list_str = list_str.strip()
    list_str = re.sub(r'\s+', ' ', list_str)
    
    # Fix common issues
    list_str = list_str.replace("'", '"')  # Single to double quotes
    list_str = re.sub(r',\s*]', ']', list_str)  # Remove trailing comma
    
    try:
        return json.loads(list_str)
    except:
        # Manual parsing
        items = []
        list_str = list_str.strip('[]')
        parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', list_str)
        
        for part in parts:
            part = part.strip()
            if part and ':' in part:
                items.append(part.strip(' "\''))
        
        return items

def convert_list_to_json(items_list: list, original_message: str) -> dict:
    """Convert extracted list to JSON structure"""
    # Default JSON structure
    result = {
        "trigger": False,
        "intent": "UNKNOWN",
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
        "next_action": "ASK_USER"
    }
    
    passenger_count = 0
    
    # Process each item in the list
    for item in items_list:
        if isinstance(item, str) and ':' in item:
            key, value = item.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            print(f"  Processing: {key}: {value}")
            
            if key == 'trigger':
                result['trigger'] = value.lower() == 'true'
                
            elif key == 'intent':
                # Map to uppercase
                intent_map = {
                    'book_ticket': 'BOOK_TICKET',
                    'cancel_ticket': 'CANCEL_TICKET',
                    'pnr_status': 'PNR_STATUS',
                    'train_schedule': 'TRAIN_SCHEDULE',
                    'seat_availability': 'SEAT_AVAILABILITY',
                    'fare_enquiry': 'FARE_ENQUIRY',
                    'add_passenger': 'ADD_PASSENGER',
                    'unknown': 'UNKNOWN'
                }
                result['intent'] = intent_map.get(value, 'UNKNOWN')
                
            elif key == 'from':
                result['slots']['from_city'] = value.title()
                
            elif key == 'to':
                result['slots']['to_city'] = value.title()
                
            elif key == 'date':
                result['slots']['journey_date'] = value
                
            elif key == 'pnr':
                result['slots']['pnr'] = value
                
            elif key == 'train':
                result['slots']['train_no'] = value
                
            elif key == 'class':
                result['slots']['class'] = value.upper()
                
            elif key == 'quota':
                result['slots']['quota'] = value.upper()
                
            elif key == 'berth':
                result['slots']['berth_preference'] = value.upper()
                
            elif key == 'passenger':
                # Parse passenger info
                parts = value.split()
                if len(parts) >= 1:
                    passenger_count += 1
                    passenger = {
                        'index': passenger_count,
                        'name': parts[0].title(),
                        'age': int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
                        'gender': parts[2].upper() if len(parts) > 2 else None,
                        'berth_preference': None
                    }
                    result['passengers'].append(passenger)
                    
                    # Update current passenger slots
                    result['slots']['passenger_index'] = passenger_count
                    result['slots']['passenger_name'] = passenger['name']
                    result['slots']['passenger_age'] = passenger['age']
                    result['slots']['passenger_gender'] = passenger['gender']
    
    # Determine missing slots
    if result['intent'] == 'BOOK_TICKET':
        missing = []
        if not result['slots']['from_city']:
            missing.append('from_city')
        if not result['slots']['to_city']:
            missing.append('to_city')
        if not result['slots']['journey_date']:
            missing.append('journey_date')
        result['missing_slots'] = missing
        
        # Set next action
        if missing:
            result['next_action'] = 'ASK_USER'
        else:
            result['next_action'] = 'READY'
            
    elif result['intent'] == 'PNR_STATUS' and not result['slots']['pnr']:
        result['missing_slots'] = ['pnr']
        result['next_action'] = 'ASK_USER'
        
    elif result['intent'] == 'CANCEL_TICKET' and not result['slots']['pnr']:
        result['missing_slots'] = ['pnr']
        result['next_action'] = 'ASK_USER'
        
    else:
        result['next_action'] = 'READY' if not result['missing_slots'] else 'ASK_USER'
    
    return result

def create_default_json() -> dict:
    """Create default JSON structure"""
    return {
        "trigger": False,
        "intent": "UNKNOWN",
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
        "next_action": "UNKNOWN"
    }

# ==================== TEST FUNCTION ====================

def test_with_modelfile():
    """Test using your Modelfile system prompt"""
    print("🧪 TESTING WITH MODELEFILE SYSTEM PROMPT")
    print("=" * 60)
    
    test_cases = [
        "book ticket from delhi to mumbai",
        "book tk from kota to agra",
        "25th jan",
        "check pnr status",
        "cancel ticket",
        "train 12951 schedule",
        "3A class",
        "lower berth",
        "actually check pnr status",
        "reset everything",
        "delhi to mumbai 15 march",
        "add passenger rahul 25 male",
        "i want to go from pune to bangalore",
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n{i}. 👤 User: '{user_input}'")
        print("-" * 40)
        
        result = get_irctc_json(user_input)
        
        print(f"\n🤖 Extracted:")
        print(f"   Intent: {result['intent']}")
        if result['slots']['from_city']:
            print(f"   From: {result['slots']['from_city']}")
        if result['slots']['to_city']:
            print(f"   To: {result['slots']['to_city']}")
        if result['slots']['journey_date']:
            print(f"   Date: {result['slots']['journey_date']}")
        if result['slots']['class']:
            print(f"   Class: {result['slots']['class']}")
        if result['slots']['berth_preference']:
            print(f"   Berth: {result['slots']['berth_preference']}")
        if result['missing_slots']:
            print(f"   Missing: {', '.join(result['missing_slots'])}")
        print(f"   Next: {result['next_action']}")

# ==================== SIMPLE USAGE ====================

def simple_usage():
    """Simple usage example"""
    # Example 1
    print("Example 1: Booking request")
    result1 = get_irctc_json("book ticket from delhi to mumbai")
    print("\nJSON Output:")
    print(json.dumps(result1, indent=2))
    
    # Example 2
    print("\n\nExample 2: Just date")
    result2 = get_irctc_json("25th jan")
    print("\nJSON Output:")
    print(json.dumps(result2, indent=2))
    
    # Example 3
    print("\n\nExample 3: Reset trigger")
    result3 = get_irctc_json("actually check pnr status")
    print("\nJSON Output:")
    print(json.dumps(result3, indent=2))

if __name__ == "__main__":
    # Run tests
    test_with_modelfile()
    
    # Or use simple example
    # simple_usage()
    
    # Or use interactively
    # while True:
    #     user_input = input("\nEnter your message (or 'quit'): ")
    #     if user_input.lower() == 'quit':
    #         break
    #     result = get_irctc_json(user_input)
    #     print("\n" + json.dumps(result, indent=2))