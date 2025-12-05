# app.py
import streamlit as st
from typing import List, Dict
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
import base64
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# -------------------------
# Configuration
# -------------------------
# Load environment variables
load_dotenv()

# Ensure DEEPSEEK_API_KEY is set in your environment
if "DEEPSEEK_API_KEY" not in os.environ:
    st.warning("Set environment variable DEEPSEEK_API_KEY before running. Example: export DEEPSEEK_API_KEY='sk-...'")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Initialize LLM via LangChain with DeepSeek
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    temperature=0,
    max_tokens=400
)

# -------------------------
# Helper functions
# -------------------------
def init_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "candidate" not in st.session_state:
        st.session_state.candidate = {}
    if "role" not in st.session_state:
        st.session_state.role = None
    if "lang" not in st.session_state:
        st.session_state.lang = "English"
    if "skills" not in st.session_state:
        st.session_state.skills = []
    if "asked_questions" not in st.session_state:
        st.session_state.asked_questions = []
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []  # list of dicts: {q, a, score, feedback}
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    if "finalized" not in st.session_state:
        st.session_state.finalized = False
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "welcome_shown" not in st.session_state:
        st.session_state.welcome_shown = False
    if "last_ai_message" not in st.session_state:
        st.session_state.last_ai_message = ""
    if "current_is_coding" not in st.session_state:
        st.session_state.current_is_coding = False
    if "question_start_time" not in st.session_state:
        st.session_state.question_start_time = None
    if "total_start_time" not in st.session_state:
        st.session_state.total_start_time = None
    if "time_expired" not in st.session_state:
        st.session_state.time_expired = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "page_redirect" not in st.session_state:
        st.session_state.page_redirect = None
    if "voice_mode" not in st.session_state:
        st.session_state.voice_mode = False
    if "audio_answer" not in st.session_state:
        st.session_state.audio_answer = None

def get_time_remaining(start_time, max_seconds):
    """Calculate remaining time in seconds"""
    if start_time is None:
        return max_seconds
    elapsed = time.time() - start_time
    remaining = max_seconds - elapsed
    return max(0, remaining)

def format_time(seconds):
    """Format seconds as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# Database functions
USERS_DB = "users.json"
EVAL_HISTORY_DB = "evaluation_history.json"

def load_users():
    """Load users from JSON database"""
    if os.path.exists(USERS_DB):
        with open(USERS_DB, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON database"""
    with open(USERS_DB, 'w') as f:
        json.dump(users, f, indent=2)

def load_eval_history():
    """Load evaluation history from JSON database"""
    if os.path.exists(EVAL_HISTORY_DB):
        with open(EVAL_HISTORY_DB, 'r') as f:
            return json.load(f)
    return {}

def save_eval_history(history):
    """Save evaluation history to JSON database"""
    with open(EVAL_HISTORY_DB, 'w') as f:
        json.dump(history, f, indent=2)

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def text_to_speech(text):
    """Convert text to speech using browser's Web Speech API"""
    # Create JavaScript code to use browser's speech synthesis
    speech_js = f"""
    <script>
    function speak() {{
        var msg = new SpeechSynthesisUtterance();
        msg.text = `{text}`;
        msg.lang = 'en-US';
        msg.rate = 0.9;
        msg.pitch = 1;
        window.speechSynthesis.speak(msg);
    }}
    speak();
    </script>
    """
    return speech_js

def create_audio_player(text, key):
    """Create an audio player button that reads text aloud"""
    # Escape special characters for JavaScript - use JSON encoding for safety
    import json
    safe_text = json.dumps(text)
    
    audio_html = f"""
    <div id="tts_container_{key}">
        <button onclick="speakText_{key}()" id="btn_{key}" style="
            background-color: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s;
            font-weight: 600;
        " onmouseover="this.style.backgroundColor='#5568d3'" onmouseout="this.style.backgroundColor='#667eea'">
            🔊 Listen to Question
        </button>
    </div>
    <script type="text/javascript">
    (function() {{
        // Ensure speech synthesis is loaded
        if ('speechSynthesis' in window) {{
            window.speakText_{key} = function() {{
                // Cancel any ongoing speech
                window.speechSynthesis.cancel();
                
                // Small delay to ensure cancel completes
                setTimeout(function() {{
                    // Create new utterance
                    var msg = new SpeechSynthesisUtterance();
                    msg.text = {safe_text};
                    msg.lang = 'en-US';
                    msg.rate = 0.85;
                    msg.pitch = 1.0;
                    msg.volume = 1.0;
                    
                    // Visual feedback
                    var btn = document.getElementById('btn_{key}');
                    if (btn) {{
                        btn.innerHTML = '🔴 Speaking...';
                        btn.style.backgroundColor = '#e74c3c';
                    }}
                    
                    msg.onend = function() {{
                        if (btn) {{
                            btn.innerHTML = '🔊 Listen to Question';
                            btn.style.backgroundColor = '#667eea';
                        }}
                    }};
                    
                    msg.onerror = function(event) {{
                        console.error('Speech synthesis error:', event);
                        if (btn) {{
                            btn.innerHTML = '🔊 Listen to Question';
                            btn.style.backgroundColor = '#667eea';
                        }}
                        alert('Speech error: ' + event.error + '. Please check your browser settings.');
                    }};
                    
                    // Load voices if not loaded yet
                    var voices = window.speechSynthesis.getVoices();
                    if (voices.length > 0) {{
                        // Try to find English voice
                        var englishVoice = voices.find(v => v.lang.startsWith('en'));
                        if (englishVoice) {{
                            msg.voice = englishVoice;
                        }}
                    }}
                    
                    // Speak
                    window.speechSynthesis.speak(msg);
                    console.log('TTS started for:', msg.text.substring(0, 50) + '...');
                }}, 100);
            }};
        }} else {{
            console.error('Speech synthesis not supported in this browser');
            var btn = document.getElementById('btn_{key}');
            if (btn) {{
                btn.innerHTML = '❌ TTS Not Supported';
                btn.disabled = true;
                btn.style.backgroundColor = '#999';
            }}
        }}
    }})();
    </script>
    """
    return audio_html

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    return stored_hash == hash_password(password)

def save_evaluation_result(username, eval_data):
    """Save evaluation result to user's history"""
    history = load_eval_history()
    if username not in history:
        history[username] = []
    
    eval_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "role": eval_data.get("role"),
        "score": eval_data.get("score"),
        "max_score": eval_data.get("max_score"),
        "percentage": eval_data.get("percentage"),
        "time_taken": eval_data.get("time_taken"),
        "qa_history": eval_data.get("qa_history", [])
    }
    
    history[username].append(eval_record)
    save_eval_history(history)

def home_page():
    # Page styling with background
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .title-box {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Title section
    st.markdown('<div class="title-box">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #667eea;'>🤖 AI-Powered Automated Candidate Evaluation System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Intelligent technical assessment with real-time AI feedback</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for Login and Register
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username.strip() or not password.strip():
                    st.error("Please provide both username and password.")
                else:
                    users = load_users()
                    if username in users and verify_password(users[username]["password"], password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.candidate = {
                            "name": users[username]["name"],
                            "experience": users[username]["experience"],
                            "email": users[username].get("email", "")
                        }
                        st.success(f"Welcome back, {users[username]['name']}! 🎉")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_username", help="Choose a unique username")
            new_name = st.text_input("Full Name", key="reg_name")
            new_email = st.text_input("Email (Optional)", key="reg_email")
            new_experience = st.selectbox("Experience Level", ["Fresher", "1-3 years", "3-6 years", "6+ years"], key="reg_exp")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            register_submitted = st.form_submit_button("Register", use_container_width=True)
            
            if register_submitted:
                if not all([new_username.strip(), new_name.strip(), new_password.strip()]):
                    st.error("Please fill in all required fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    users = load_users()
                    if new_username in users:
                        st.error("Username already exists. Please choose a different one.")
                    else:
                        users[new_username] = {
                            "name": new_name.strip(),
                            "email": new_email.strip(),
                            "experience": new_experience,
                            "password": hash_password(new_password),
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_users(users)
                        st.success(f"Account created successfully! Welcome, {new_name}! 🎉")
                        st.info("Please login using the Login tab.")
    
    # Features section
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🎯 Smart Evaluation")
        st.write("AI-powered question generation tailored to your role and skills")
    with col2:
        st.markdown("### ⏱️ Timed Assessment")
        st.write("10 minutes per question with real-time timer tracking")
    with col3:
        st.markdown("### 📊 Instant Feedback")
        st.write("Get detailed scores and improvement suggestions immediately")

def build_question_prompt(role: str, skills: List[str], language: str, is_coding: bool = False, asked_questions: List[str] = None):
    # Template that asks the LLM to produce role-specific technical questions
    previous_questions = ""
    if asked_questions:
        previous_questions = f"\n\nIMPORTANT: Do NOT repeat these previously asked questions: {', '.join(asked_questions)}\nGenerate a completely DIFFERENT question."
    
    if is_coding:
        template = (
            "You are an interview generator for the role of {role}. "
            "The candidate's listed skills: {skills}. "
            "Generate one UNIQUE coding problem or algorithm question that requires writing actual code. "
            "The question should ask the candidate to write a function, method, or code snippet. "
            "Make it practical and relevant to the role. "
            "Do not include answer or explanation. Output ONLY the question text. "
            f"Respond in {{language}}.{previous_questions}"
        )
    else:
        template = (
            "You are an interview generator for the role of {role}. "
            "The candidate's listed skills: {skills}. "
            "Generate one UNIQUE theoretical or conceptual technical question (not a behavioral question) that tests these skills. "
            "Focus on concepts, design patterns, best practices, or architecture. "
            "Do not include answer or explanation. Output ONLY the question text. "
            f"Respond in {{language}}.{previous_questions}"
        )
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["role", "skills", "language"]
    )
    return prompt

def build_evaluator_prompt(role: str, skill_focus: str, question: str, candidate_answer: str, language: str, is_coding: bool = False):
    # Prompt the LLM to evaluate candidate answer and give numeric score 0-20 & short feedback.
    if is_coding:
        template = (
            "You are a strict technical interviewer/evaluator for the role of {role}. "
            "Skill focus: {skill_focus}. "
            "Question: {question}\n\n"
            "Candidate answer: {candidate_answer}\n\n"
            "This is a CODING question. Evaluate the code based on:\n"
            "1. Correctness - Does the code solve the problem? (8 points)\n"
            "2. Code Quality - Is it readable, well-structured? (4 points)\n"
            "3. Efficiency - Is the approach optimal? (4 points)\n"
            "4. Edge cases - Are they handled? (4 points)\n\n"
            "In {language}, provide a numeric score between 0 and 20 (20 = perfect). "
            "Include a reason explaining the score and 1-2 specific suggestions to improve the code. "
            "If no code is provided or answer is off-topic, give 0 points. "
            "Output in JSON with keys: score, reason, suggestions. "
        )
    else:
        template = (
            "You are a strict technical interviewer/evaluator for the role of {role}. "
            "Skill focus: {skill_focus}. "
            "Question: {question}\n\n"
            "Candidate answer: {candidate_answer}\n\n"
            "In {language}, first evaluate whether the answer addresses the technical requirements. "
            "Then give a numeric score between 0 and 20 (20 = perfect), followed by a one-sentence reason and 1-2 suggestions to improve. "
            "If the answer is off-topic, say it is off-topic and give 0 points. "
            "Output in JSON with keys: score, reason, suggestions. "
        )
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["role", "skill_focus", "question", "candidate_answer", "language"]
    )
    return prompt

def gen_question(role: str, skills: List[str], language: str, question_num: int = 1, asked_questions: List[str] = None) -> tuple:
    # Questions 3 and 5 will be coding questions
    is_coding = question_num in [3, 5]
    prompt = build_question_prompt(role, ", ".join(skills), language, is_coding, asked_questions)
    
    # Use temperature > 0 for variety in questions
    varied_llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        temperature=0.7,  # Add randomness to avoid repetition
        max_tokens=400
    )
    chain = prompt | varied_llm | StrOutputParser()
    question = chain.invoke({"role": role, "skills": ", ".join(skills), "language": language})
    return question.strip().strip('"'), is_coding

def evaluate_answer(role: str, skill_focus: str, question: str, answer: str, language: str, is_coding: bool = False) -> Dict:
    prompt = build_evaluator_prompt(role, skill_focus, question, answer, language, is_coding)
    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({"role": role, "skill_focus": skill_focus, "question": question, "candidate_answer": answer, "language": language})
    # Try to parse simple "score: X" or JSON-like output; we'll be permissive
    # Expecting a JSON-like, but if not, we fallback to parsing digits.
    try:
        # attempt to find JSON substring
        jtext = res[res.find("{"):res.rfind("}")+1]
        parsed = json.loads(jtext)
        parsed['raw'] = res
        return parsed
    except Exception:
        # fallback: try to extract first integer 0-20
        m = re.search(r"(\b[0-1]?\d|20)\b", res)
        score = int(m.group(0)) if m else 0
        return {"score": score, "reason": res[:200], "suggestions": "", "raw": res}

# -------------------------
# UI
# -------------------------
st.set_page_config(
    page_title="AI Candidate Evaluation System", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_state()

# Sidebar navigation
if st.session_state.logged_in:
    st.sidebar.success(f"👤 Logged in as: **{st.session_state.candidate.get('name')}**")
    menu = ["Home", "New Evaluation", "Evaluation History", "Results"]
    if st.sidebar.button("🚪 Logout"):
        # Save current evaluation if exists
        if st.session_state.finalized and st.session_state.qa_history:
            total_score = sum([q["score"] for q in st.session_state.qa_history])
            max_score = 20 * len(st.session_state.qa_history)
            time_taken = time.time() - st.session_state.total_start_time if st.session_state.total_start_time else 0
            save_evaluation_result(st.session_state.username, {
                "role": st.session_state.role,
                "score": total_score,
                "max_score": max_score,
                "percentage": (total_score / max_score * 100) if max_score else 0,
                "time_taken": time_taken,
                "qa_history": st.session_state.qa_history
            })
        
        # Clear session
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
else:
    menu = ["Home"]

choice = st.sidebar.selectbox("📋 Navigation", menu)

if choice == "Home":
    if not st.session_state.logged_in:
        home_page()
    else:
        st.title("🏠 Dashboard")
        st.write(f"Welcome back, **{st.session_state.candidate.get('name')}**!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📝 Start a new evaluation from the **New Evaluation** page")
        with col2:
            history = load_eval_history()
            user_evals = history.get(st.session_state.username, [])
            st.metric("🎯 Total Evaluations", len(user_evals))
        with col3:
            if user_evals:
                avg_score = sum([e["percentage"] for e in user_evals]) / len(user_evals)
                st.metric("📊 Average Score", f"{avg_score:.1f}%")
        
        st.markdown("---")
        st.subheader("Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start New Evaluation", use_container_width=True):
                st.session_state.page_redirect = "New Evaluation"
                st.rerun()
        with col2:
            if st.button("📜 View Evaluation History", use_container_width=True):
                st.session_state.page_redirect = "Evaluation History"
                st.rerun()

elif choice == "New Evaluation":
    if not st.session_state.logged_in:
        st.info("Please login first from the Home page.")
        st.stop()

    st.header("Candidate Evaluation")
    st.markdown(f"**Candidate:** {st.session_state.candidate.get('name')}  •  **Experience:** {st.session_state.candidate.get('experience')}")
    with st.form("setup_form"):
        role = st.selectbox("Choose role", ["Java Developer", "Database Administrator", "Frontend Developer", "DevOps Engineer", "Data Engineer", "Python Developer"])
        language = st.selectbox("Preferred language / Multilingual", ["English", "Hindi", "Spanish", "German", "French"])
        skills_text = st.text_input("Main technical skills (comma-separated). Example: Spring Boot, REST, SQL, Kafka")
        start = st.form_submit_button("Start Evaluation")
        if start:
            st.session_state.role = role
            st.session_state.lang = language
            skills = [s.strip() for s in skills_text.split(",") if s.strip()]
            if not skills:
                st.warning("Please list at least one skill to focus the interview.")
            else:
                st.session_state.skills = skills
                st.session_state.asked_questions = []
                st.session_state.qa_history = []
                st.session_state.question_count = 0
                st.session_state.finalized = False
                st.session_state.welcome_shown = False  # Reset welcome for new evaluation
                st.session_state.current_question = ""
                st.session_state.question_start_time = None
                st.session_state.total_start_time = time.time()  # Start total timer
                st.session_state.time_expired = False
                st.success("Setup complete. Scroll down to the chat below.")
                st.rerun()

    # Chat / interview UI
    if st.session_state.role and st.session_state.skills:
        st.subheader("Interview Chat")
        
        # Welcome message from AI (once)
        if not st.session_state.welcome_shown:
            welcome_text = f"Welcome {st.session_state.candidate.get('name')}! 👋\n\n"
            welcome_text += f"I'm your AI interviewer for the {st.session_state.role} position. "
            welcome_text += f"We will conduct a technical evaluation with 5 questions focusing on your skills: {', '.join(st.session_state.skills)}.\n\n"
            welcome_text += "📋 **Interview Format:**\n"
            welcome_text += "- Questions 1-2: Theoretical/Conceptual\n"
            welcome_text += "- Question 3: Coding Problem 💻\n"
            welcome_text += "- Question 4: Theoretical/Conceptual\n"
            welcome_text += "- Question 5: Coding Problem 💻\n\n"
            welcome_text += "Please answer each question to the best of your ability. You'll receive a score and feedback after each answer. Let's begin!"
            
            st.session_state.welcome_shown = True
            st.session_state.last_ai_message = welcome_text
            
            # Generate first question
            first_q, is_coding = gen_question(st.session_state.role, st.session_state.skills, st.session_state.lang, question_num=1, asked_questions=[])
            st.session_state.asked_questions.append(first_q)
            st.session_state.question_count = 1
            st.session_state.current_question = first_q
            st.session_state.current_is_coding = is_coding
            st.session_state.question_start_time = time.time()  # Start timer for first question
        
        # Check total time (50 minutes max)
        total_time_remaining = get_time_remaining(st.session_state.total_start_time, 50 * 60)
        if total_time_remaining <= 0 and not st.session_state.finalized:
            st.session_state.finalized = True
            st.session_state.time_expired = True
            st.error("⏰ Time's up! Total interview time (50 minutes) has expired.")
            st.info("👉 Please go to the **Results** page to see your evaluation.")
            st.stop()
        
        # Display total timer with auto-refresh
        col1, col2 = st.columns([3, 1])
        with col2:
            if not st.session_state.finalized:
                timer_placeholder = st.empty()
                timer_placeholder.metric("⏱️ Total Time Left", format_time(total_time_remaining))
        
        # Display welcome message
        if st.session_state.last_ai_message and not st.session_state.qa_history:
            st.info(st.session_state.last_ai_message)
        
        # Show previous QA history first (older questions at top)
        if st.session_state.qa_history:
            st.markdown("### 📝 Interview Progress:")
            for idx, qa in enumerate(st.session_state.qa_history, start=1):
                # Determine if this was a coding question (questions 3 and 5)
                q_type_icon = "💻" if idx in [3, 5] else "💭"
                with st.expander(f"{q_type_icon} Question {idx} - Score: {qa.get('score')}/20", expanded=False):
                    st.markdown(f"**Q:** {qa['q']}")
                    st.markdown(f"**Your Answer:** {qa['a']}")
                    st.markdown(f"**Feedback:** {qa.get('feedback')}")
            st.markdown("---")
        
        # Voice mode toggle
        st.markdown("---")
        col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
        with col_v2:
            voice_enabled = st.toggle("🎤 Voice Mode", value=st.session_state.voice_mode, help="Enable voice input/output")
            if voice_enabled != st.session_state.voice_mode:
                st.session_state.voice_mode = voice_enabled
                st.rerun()
        with col_v3:
            # Test TTS button
            if st.session_state.voice_mode:
                test_button_html = """
                <button onclick="testTTS()" style="
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                ">
                    🔊 Test TTS
                </button>
                <script type="text/javascript">
                function testTTS() {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        setTimeout(function() {
                            var testMsg = new SpeechSynthesisUtterance();
                            testMsg.text = 'Text to speech is working correctly! Hello from the AI evaluation system.';
                            testMsg.lang = 'en-US';
                            testMsg.rate = 0.9;
                            testMsg.pitch = 1;
                            testMsg.volume = 1;
                            
                            testMsg.onstart = function() {
                                console.log('TTS test started');
                            };
                            
                            testMsg.onend = function() {
                                console.log('TTS test completed');
                            };
                            
                            testMsg.onerror = function(event) {
                                console.error('TTS test error:', event);
                                alert('TTS Error: ' + event.error);
                            };
                            
                            window.speechSynthesis.speak(testMsg);
                        }, 100);
                    } else {
                        alert('Speech synthesis is not supported in your browser');
                    }
                }
                </script>
                """
                st.markdown(test_button_html, unsafe_allow_html=True)
                st.caption("Click to test if audio works")
        
        # Display current question (newest at bottom)
        if st.session_state.current_question and st.session_state.question_count > 0 and st.session_state.question_count <= 5:
            # Check question time (10 minutes max per question)
            question_time_remaining = get_time_remaining(st.session_state.question_start_time, 10 * 60)
            
            question_type = "💻 Coding Question" if st.session_state.current_is_coding else "💭 Conceptual Question"
            st.markdown(f"### ❓ Question {st.session_state.question_count}: {question_type}")
            
            # Display question timer
            col1, col2, col3 = st.columns([3, 1, 0.5])
            with col1:
                st.markdown(f"**{st.session_state.current_question}**")
                
                # Add text-to-speech button for the question
                if st.session_state.voice_mode:
                    # Use both approaches for better compatibility
                    col_tts1, col_tts2 = st.columns([1, 3])
                    with col_tts1:
                        # HTML-based TTS button
                        st.markdown(create_audio_player(st.session_state.current_question, f"q{st.session_state.question_count}"), unsafe_allow_html=True)
                    with col_tts2:
                        st.caption("💡 Click the button above to hear the question read aloud")
            
            with col2:
                timer_color = "🟢" if question_time_remaining > 300 else "🟡" if question_time_remaining > 60 else "🔴"
                st.metric(f"{timer_color} Question Timer", format_time(question_time_remaining))
            with col3:
                if st.button("🔄", help="Refresh timer"):
                    st.rerun()

        # Candidate answer input
        if not st.session_state.finalized:
            # Check if question time expired
            question_time_remaining = get_time_remaining(st.session_state.question_start_time, 10 * 60)
            
            # Voice input section (outside form)
            if st.session_state.voice_mode:
                st.markdown("#### 🎤 Voice Input")
                
                if AUDIO_AVAILABLE:
                    st.info("💡 Click the microphone button below to record your answer, or type it manually.")
                    
                    col_mic1, col_mic2 = st.columns([2, 1])
                    with col_mic1:
                        audio_bytes = audio_recorder(
                            text="Click to record",
                            recording_color="#e74c3c",
                            neutral_color="#667eea",
                            icon_name="microphone",
                            icon_size="3x",
                            key=f"audio_recorder_{st.session_state.question_count}"
                        )
                        
                        if audio_bytes:
                            st.success("✅ Audio recorded! Converting to text...")
                            st.info("Note: For production, integrate with Google Speech-to-Text or Whisper API for accurate transcription.")
                            st.session_state.audio_answer = "[Voice answer recorded - transcription would appear here with Speech-to-Text API]"
                    with col_mic2:
                        if st.button("🗑️ Clear Recording"):
                            st.session_state.audio_answer = None
                            st.rerun()
                else:
                    st.warning("⚠️ Voice recording library not installed. Using browser-based alternative...")
                    
                    # Fallback: HTML5 audio recording
                    st.markdown("""
                    <div style="padding: 20px; background: #f0f2f6; border-radius: 10px; margin: 10px 0;">
                        <button onclick="startRecording()" id="recordBtn" style="
                            background-color: #667eea;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            margin: 5px;
                        ">
                            🎙️ Start Recording
                        </button>
                        <button onclick="stopRecording()" id="stopBtn" style="
                            background-color: #e74c3c;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            margin: 5px;
                            display: none;
                        ">
                            ⏹️ Stop Recording
                        </button>
                        <div id="status" style="margin-top: 10px; font-weight: bold;"></div>
                    </div>
                    <script>
                    let mediaRecorder;
                    let audioChunks = [];
                    
                    async function startRecording() {
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            mediaRecorder = new MediaRecorder(stream);
                            audioChunks = [];
                            
                            mediaRecorder.ondataavailable = (event) => {
                                audioChunks.push(event.data);
                            };
                            
                            mediaRecorder.onstop = () => {
                                document.getElementById('status').innerHTML = '✅ Recording saved! You can now type your answer below or re-record.';
                            };
                            
                            mediaRecorder.start();
                            document.getElementById('recordBtn').style.display = 'none';
                            document.getElementById('stopBtn').style.display = 'inline-block';
                            document.getElementById('status').innerHTML = '🔴 Recording in progress...';
                        } catch (err) {
                            document.getElementById('status').innerHTML = '❌ Microphone access denied. Please allow microphone access.';
                        }
                    }
                    
                    function stopRecording() {
                        mediaRecorder.stop();
                        mediaRecorder.stream.getTracks().forEach(track => track.stop());
                        document.getElementById('recordBtn').style.display = 'inline-block';
                        document.getElementById('stopBtn').style.display = 'none';
                    }
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.info("ℹ️ After recording, type your answer in the text box below. For production, install: `pip install audio-recorder-streamlit`")
                    
                    if st.button("🗑️ Clear Recording"):
                        st.session_state.audio_answer = None
                        st.rerun()
                
                st.markdown("---")
            
            with st.form("answer_form", clear_on_submit=True):
                # Pre-fill with audio transcription if available
                default_text = st.session_state.audio_answer if st.session_state.audio_answer else ""
                placeholder_text = "Write your code here..." if st.session_state.current_is_coding else "Type your answer here (or use voice input above)..."
                answer = st.text_area("Your answer", value=default_text, key="answer_area", height=200 if st.session_state.current_is_coding else 150, placeholder=placeholder_text)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    submit_ans = st.form_submit_button("Submit Answer", type="primary")
                with col2:
                    skip_ans = st.form_submit_button("Skip / Don't Know")
                
                # Handle timeout
                if question_time_remaining <= 0:
                    st.warning("⏰ Time's up for this question! Auto-submitting...")
                    answer = answer if answer.strip() else "[No answer provided - Time expired]"
                    submit_ans = True
                
                if submit_ans or skip_ans:
                    if skip_ans:
                        answer = "[Skipped - Don't know]"
                    elif not answer.strip():
                        st.error("Please provide an answer before submitting.")
                        st.stop()
                    
                    # Evaluate answer
                    q = st.session_state.current_question
                    skill_focus = st.session_state.skills[0]  # for simplicity, focus on first skill (could be rotated)
                    is_coding = st.session_state.current_is_coding
                    
                    spinner_text = "🤔 Evaluating your code..." if is_coding else "🤔 Evaluating your answer..."
                    with st.spinner(spinner_text):
                        eval_result = evaluate_answer(st.session_state.role, skill_focus, q, answer, st.session_state.lang, is_coding)
                    
                    # Parse evaluation results
                    score = int(eval_result.get("score", 0))
                    reason = eval_result.get("reason", "") or eval_result.get("raw", "")
                    suggestions = eval_result.get("suggestions", "")
                    
                    # Save to history
                    st.session_state.qa_history.append({
                        "q": q, "a": answer, "score": score, "feedback": f"{reason} {suggestions}"
                    })
                    
                    # Display immediate feedback
                    st.markdown("---")
                    st.markdown("### 📊 Evaluation Result")
                    
                    # Score display with color coding
                    if score >= 16:
                        st.success(f"**Score: {score}/20** - Excellent! ✅")
                    elif score >= 12:
                        st.info(f"**Score: {score}/20** - Good! 👍")
                    elif score >= 8:
                        st.warning(f"**Score: {score}/20** - Fair ⚠️")
                    else:
                        st.error(f"**Score: {score}/20** - Needs Improvement 📚")
                    
                    # Detailed feedback
                    st.markdown(f"**💬 Feedback:** {reason}")
                    if suggestions:
                        st.markdown(f"**💡 Suggestions:** {suggestions}")
                    
                    st.markdown("---")
                    
                    # Check if interview is complete or move to next question
                    if st.session_state.question_count >= 5:
                        st.session_state.finalized = True
                        
                        # Save evaluation to history
                        total_score = sum([q["score"] for q in st.session_state.qa_history])
                        max_score = 20 * len(st.session_state.qa_history)
                        time_taken = time.time() - st.session_state.total_start_time if st.session_state.total_start_time else 0
                        save_evaluation_result(st.session_state.username, {
                            "role": st.session_state.role,
                            "score": total_score,
                            "max_score": max_score,
                            "percentage": (total_score / max_score * 100) if max_score else 0,
                            "time_taken": time_taken,
                            "qa_history": st.session_state.qa_history
                        })
                        
                        st.balloons()
                        st.success("🎉 Interview complete! You've answered all 5 questions.")
                        st.info("👉 Please go to the **Results** page to see your final evaluation.")
                    else:
                        # Generate next question
                        next_q_num = st.session_state.question_count + 1
                        with st.spinner("Preparing next question..."):
                            tries = 0
                            new_q = ""
                            new_is_coding = False
                            while tries < 8:
                                tries += 1
                                candidate_q, new_is_coding = gen_question(
                                    st.session_state.role, 
                                    st.session_state.skills, 
                                    st.session_state.lang, 
                                    question_num=next_q_num,
                                    asked_questions=st.session_state.asked_questions
                                )
                                # Check if question is truly unique (not just different wording)
                                is_duplicate = False
                                for asked in st.session_state.asked_questions:
                                    # Simple similarity check - if more than 50% of words match, consider it duplicate
                                    asked_words = set(asked.lower().split())
                                    candidate_words = set(candidate_q.lower().split())
                                    if len(asked_words) > 0:
                                        overlap = len(asked_words.intersection(candidate_words)) / len(asked_words)
                                        if overlap > 0.5:
                                            is_duplicate = True
                                            break
                                
                                if not is_duplicate:
                                    new_q = candidate_q
                                    break
                            
                            if not new_q:
                                # Fallback question if generation fails
                                if next_q_num in [3, 5]:
                                    new_q = f"Write a function to solve a common problem using {st.session_state.skills[0]}."
                                    new_is_coding = True
                                else:
                                    new_q = f"Explain an advanced concept or best practice related to {st.session_state.skills[0]}."
                                    new_is_coding = False
                            
                            st.session_state.asked_questions.append(new_q)
                            st.session_state.current_question = new_q
                            st.session_state.current_is_coding = new_is_coding
                            st.session_state.question_count = next_q_num
                            st.session_state.question_start_time = time.time()  # Reset timer for new question
                            st.session_state.audio_answer = None  # Clear previous audio recording
                        
                        st.success(f"✅ Moving to Question {st.session_state.question_count}...")
                        time.sleep(1.5)  # Brief pause before refresh
                        st.rerun()

elif choice == "Evaluation History":
    if not st.session_state.logged_in:
        st.info("Please login first from the Home page.")
        st.stop()
    
    st.title("📜 Evaluation History")
    st.markdown(f"**User:** {st.session_state.candidate.get('name')}")
    
    history = load_eval_history()
    user_evals = history.get(st.session_state.username, [])
    
    if not user_evals:
        st.info("No evaluation history found. Complete your first evaluation to see results here!")
        if st.button("🚀 Start New Evaluation"):
            st.session_state.page_redirect = "New Evaluation"
            st.rerun()
    else:
        st.success(f"You have completed **{len(user_evals)}** evaluation(s)")
        
        # Display evaluations in reverse chronological order (newest first)
        for idx, eval_data in enumerate(reversed(user_evals), 1):
            with st.expander(f"📝 Evaluation #{len(user_evals) - idx + 1} - {eval_data['date']} - {eval_data['role']}", expanded=(idx==1)):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Role", eval_data['role'])
                with col2:
                    st.metric("Score", f"{eval_data['score']}/{eval_data['max_score']}")
                with col3:
                    st.metric("Percentage", f"{eval_data['percentage']:.1f}%")
                with col4:
                    st.metric("Time", format_time(eval_data['time_taken']))
                
                st.markdown("---")
                st.subheader("Question-wise Performance:")
                
                for q_idx, qa in enumerate(eval_data['qa_history'], 1):
                    q_type_icon = "💻" if q_idx in [3, 5] else "💭"
                    with st.container():
                        st.markdown(f"**{q_type_icon} Question {q_idx}:** {qa['q']}")
                        st.markdown(f"**Your Answer:** {qa['a']}")
                        score_color = "🟢" if qa['score'] >= 16 else "🟡" if qa['score'] >= 12 else "🟠" if qa['score'] >= 8 else "🔴"
                        st.markdown(f"**{score_color} Score:** {qa['score']}/20")
                        st.markdown(f"**Feedback:** {qa['feedback']}")
                        st.markdown("---")

elif choice == "Results":
    if not st.session_state.logged_in:
        st.info("Please login first on the Login page.")
        st.stop()
    st.header("Interview Results")
    total_score = sum([q["score"] for q in st.session_state.qa_history])
    max_score = 20 * max(1, len(st.session_state.qa_history))
    pct = (total_score / max_score) * 100 if max_score else 0
    
    # Calculate time taken
    time_taken = 0
    if st.session_state.total_start_time:
        time_taken = time.time() - st.session_state.total_start_time
    
    st.markdown(f"**Candidate:** {st.session_state.candidate.get('name')}")
    st.markdown(f"**Role:** {st.session_state.role}  •  **Language:** {st.session_state.lang}")
    
    # Display time info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total Score", f"{total_score} / {max_score} ({pct:.1f}%)")
    with col2:
        st.metric("⏱️ Time Taken", format_time(time_taken))
    
    if st.session_state.time_expired:
        st.warning("⚠️ Note: Interview was terminated due to timeout (50 minutes exceeded).")
    
    st.markdown("---")
    st.markdown("### 📋 Detailed Question-wise Performance")
    for i, qa in enumerate(st.session_state.qa_history, start=1):
        q_type_icon = "💻" if i in [3, 5] else "💭"
        score_color = "🟢" if qa['score'] >= 16 else "🟡" if qa['score'] >= 12 else "🟠" if qa['score'] >= 8 else "🔴"
        with st.expander(f"{q_type_icon} Question {i} - {score_color} Score: {qa['score']}/20", expanded=False):
            st.markdown(f"**Q:** {qa['q']}")
            st.markdown(f"**Your Answer:** {qa['a']}")
            st.markdown(f"**Feedback:** {qa['feedback']}")

    st.markdown("---")
    
    # Final Recommendation Section
    st.markdown("## 🎯 Final Recommendation")
    
    # Check if evaluation is complete (all 5 questions answered)
    if len(st.session_state.qa_history) < 5:
        st.info("⏳ **Evaluation in Progress**")
        st.write(f"Completed: {len(st.session_state.qa_history)}/5 questions")
        st.write("Please complete all questions to receive your final recommendation.")
    else:
        # Generate AI-powered recommendation
        with st.spinner("🤖 Generating detailed recommendation..."):
            # Prepare summary for AI
            qa_summary = ""
            for i, qa in enumerate(st.session_state.qa_history, 1):
                qa_summary += f"Q{i} (Score: {qa['score']}/20): {qa['q'][:100]}... Answer quality: {qa['feedback'][:150]}...\n"
            
            recommendation_prompt = PromptTemplate(
                template=(
                    "You are a senior technical hiring manager evaluating a candidate for {role} position.\n\n"
                    "Candidate Performance Summary:\n"
                    "- Total Score: {total_score}/{max_score} ({percentage:.1f}%)\n"
                    "- Questions Answered: 5 (2 conceptual, 2 coding, 1 conceptual)\n"
                    "- Time Taken: {time_taken} minutes\n\n"
                    "Question-wise breakdown:\n{qa_summary}\n\n"
                    "Based on this performance, provide:\n"
                    "1. Clear recommendation: RECOMMENDED or NOT RECOMMENDED\n"
                    "2. 2-3 key strengths observed\n"
                    "3. 2-3 areas for improvement\n"
                    "4. Brief rationale (2-3 sentences) explaining your recommendation\n\n"
                    "Be professional, constructive, and specific. Format your response clearly."
                ),
                input_variables=["role", "total_score", "max_score", "percentage", "time_taken", "qa_summary"]
            )
            
            chain = recommendation_prompt | llm | StrOutputParser()
            recommendation = chain.invoke({
                "role": st.session_state.role,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": pct,
                "time_taken": f"{int(time_taken // 60)}:{int(time_taken % 60):02d}",
                "qa_summary": qa_summary
            })
            
            # Display recommendation with styling
            if "RECOMMENDED" in recommendation.upper() and "NOT RECOMMENDED" not in recommendation.upper():
                st.success("✅ **Candidate is RECOMMENDED for this role**")
            else:
                st.error("❌ **Candidate is NOT RECOMMENDED for this role**")
            
            st.markdown(recommendation)
    
    st.markdown("---")
    
    # Export results button
    if len(st.session_state.qa_history) == 5:
        if st.button("📥 Export Complete Evaluation Report", use_container_width=True):
            import io
            out = io.StringIO()
            out.write("="*60 + "\n")
            out.write("CANDIDATE EVALUATION REPORT\n")
            out.write("="*60 + "\n\n")
            out.write(f"Candidate: {st.session_state.candidate.get('name')}\n")
            out.write(f"Role: {st.session_state.role}\n")
            out.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write(f"Total Score: {total_score}/{max_score} ({pct:.1f}%)\n")
            out.write(f"Time Taken: {format_time(time_taken)}\n\n")
            out.write("="*60 + "\n")
            out.write("QUESTION-WISE PERFORMANCE\n")
            out.write("="*60 + "\n\n")
            for i, qa in enumerate(st.session_state.qa_history, start=1):
                out.write(f"Q{i}: {qa['q']}\n")
                out.write(f"Answer: {qa['a']}\n")
                out.write(f"Score: {qa['score']}/20\n")
                out.write(f"Feedback: {qa['feedback']}\n")
                out.write("-"*60 + "\n\n")
            
            filename = f"evaluation_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            st.download_button("📄 Download Report", out.getvalue(), file_name=filename, mime="text/plain")
