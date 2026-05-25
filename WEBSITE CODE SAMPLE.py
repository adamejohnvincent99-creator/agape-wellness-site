from flask import Flask, render_template, request
import requests
import google.generativeai as genai
from abc import ABC, abstractmethod

# --- 1. CONFIGURE GEMINI AI ---
genai.configure(api_key="AIzaSyBpX7oYOiAYakqB81Edp0n8EgHn0rgu_Gk")

# THE BULLETPROOF FIX: Automatically find a valid model for your API key
valid_model_name = 'gemini-1.0-pro' # Fallback name
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            valid_model_name = m.name
            break
except Exception as e:
    print(f"Error fetching models: {e}")

model = genai.GenerativeModel(valid_model_name)

app = Flask(__name__)

# --- 2. OOP BACKEND LOGIC ---
class WellnessResource(ABC):
    def __init__(self, title, description):
        self.title = title
        self.description = description

class Practice(WellnessResource):
    def __init__(self, title, description, duration_minutes):
        super().__init__(title, description)
        self.__duration_minutes = duration_minutes

    def get_duration(self):
        return self.__duration_minutes

class Advice(WellnessResource):
    def __init__(self, title, description, category):
        super().__init__(title, description)
        self.category = category

# --- 3. GENERATING OUR DATA ---
def get_wellness_data():
    mental_advice = [
        Advice("Embrace Self-Compassion", "Treat yourself with the same kindness you would offer a dear friend.", "Mental Health"),
        Advice("Set Healthy Boundaries", "Protect your energy by learning to say no. Boundaries are clear lines that allow you to engage safely.", "Relationships"),
        Advice("Digital Detoxification", "Constantly absorbing information can overwhelm the nervous system. Dedicate time to disconnect.", "Lifestyle")
    ]
    
    healing_practices = [
        Practice("Breathwork (Pranayama)", "Try the 4-7-8 method.", 5),
        Practice("Mindful Journaling", "Write a 'brain dump.' Pour anxieties onto paper.", 10),
        Practice("Grounding (Earthing)", "Walk barefoot on natural surfaces to reconnect.", 15)
    ]
    
    return mental_advice, healing_practices

# --- 4. EMERGENCY CRISIS LOGIC ---
def check_for_emergency(situation_text):
    text = situation_text.lower()
    emergency_keywords = [
        "suicide", "kill myself", "want to die", "end it", "give up", 
        "can't do this anymore", "life so hard", "died", "passed away", 
        "grief", "lost my", "dead"
    ]
    
    for keyword in emergency_keywords:
        if keyword in text:
            return [
                {"name": "NCMH Crisis Hotline (24/7)", "details": "1553 (Luzon-wide) | 0917-899-8727", "url": "https://ncmh.gov.ph/"},
                {"name": "Hopeline Philippines (24/7)", "details": "0917-558-4673 | 0918-873-4673", "url": "https://www.facebook.com/HopelinePH/"}
            ]
    return None

# --- 5. EXTERNAL API BIBLE VERSE LOGIC ---
def get_comforting_verse(situation_text):
    text = situation_text.lower()
    references = {
        "overwhelm": "Matthew+11:28", "anxi": "Philippians+4:6", 
        "sad": "Psalm+34:18", "hard": "John+16:33", "died": "Matthew+5:4", 
        "grief": "Revelation+21:4"
    }
    
    selected_reference = "John+14:27" 
    for keyword, ref in references.items():
        if keyword in text:
            selected_reference = ref
            break
            
    try:
        response = requests.get(f"https://bible-api.com/{selected_reference}")
        if response.status_code == 200:
            data = response.json()
            return f"“{data['text'].strip()}” - {data['reference']}"
    except Exception:
        pass 
        
    return "“Peace I leave with you; my peace I give you. Do not let your hearts be troubled.” - John 14:27"

# --- 6. AI LOGIC (WITH VERSE EXPLANATION) ---
def get_validation_data(situation_text, verse_text):
    """Sends the situation AND the verse to Gemini for a 3-part response."""
    
    prompt = f"""
    You are Agape, a highly advanced, compassionate psychological and spiritual guide. 
    A user has shared this vulnerability: '{situation_text}'.
    We are sharing this Bible verse with them: '{verse_text}'.
    
    Analyze their feelings and provide a 3-part response separated by a single pipe symbol (|).
    
    Part 1: The exact clinical psychological term for their feelings (e.g., Acute Grief, Somatic Anxiety, Depressive Mood, Burnout).
    Part 2: A deeply empathetic paragraph validating them, followed by one realistic micro-step they can take right now. Use <br> and <b> for formatting. Do NOT use markdown.
    Part 3: A brief, beautiful explanation of exactly how that specific Bible verse connects to their current struggle.
    
    FORMAT EXACTLY LIKE THIS:
    Clinical Term | Your empathetic message and micro-step. | Your explanation of the verse.
    """
    
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.85))
        parts = response.text.split('|') 
        
        if len(parts) >= 3:
            return {
                "term": parts[0].strip(), 
                "message": parts[1].strip(),
                "verse_explanation": parts[2].strip()
            }
        else:
            return {"term": "Emotional Support", "message": response.text.replace("|", ""), "verse_explanation": "May these words bring you comfort and peace."}
            
    except Exception as e:
        print(f"------------ AI CONNECTION ERROR ------------\n{e}\n---------------------------------------------")
        return {
            "term": "Connection Error", 
            "message": f"We hear you, and your feelings are entirely valid. <br><br><i>(Note for Vincent: The AI connection failed! Error: {e})</i>",
            "verse_explanation": ""
        }

# --- 7. EXTERNAL WELLNESS RESOURCES LOGIC ---
def get_helpful_resources(situation_text):
    return [
        {"name": "Mental Health America (MHA)", "url": "https://mhanational.org/"},
        {"name": "7 Cups: Free Emotional Support & Chat", "url": "https://www.7cups.com/"}
    ]

# --- 8. FLASK ROUTING WITH FORM HANDLING ---
@app.route('/', methods=['GET', 'POST'])
def home():
    advice_list, practice_list = get_wellness_data()
    
    user_name = None
    user_situation = None
    bible_verse = None
    user_resources = None 
    emergency_hotlines = None 
    validation_data = None 
    
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        user_situation = request.form.get('user_situation')
        
        if user_situation:
            emergency_hotlines = check_for_emergency(user_situation)
            
            # 1. Fetch the verse FIRST
            bible_verse = get_comforting_verse(user_situation)
            
            # 2. Pass BOTH the situation and the verse to the AI
            validation_data = get_validation_data(user_situation, bible_verse) 
            
            user_resources = get_helpful_resources(user_situation)
        
    return render_template(
        'index.html', 
        advice_data=advice_list, 
        practice_data=practice_list,
        user_name=user_name,
        user_situation=user_situation,
        validation_data=validation_data, 
        bible_verse=bible_verse,
        user_resources=user_resources,
        emergency_hotlines=emergency_hotlines 
    )

if __name__ == '__main__':
    app.run(debug=True)