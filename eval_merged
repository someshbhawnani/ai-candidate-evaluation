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
import httpx
# audio recorder integration removed - recording section cleaned up

# -------------------------
# Configuration
# -------------------------
# Load environment variables
load_dotenv()

# Ensure Python/requests/ssl use a readable CA bundle inside the venv
# This prevents PermissionError when a system `SSL_CERT_FILE` points to
# an administrator-only file (e.g. C:\\Users\\Administrator\\cacert.pem).
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    # If certifi isn't available for some reason, continue — the earlier
    # behavior (using system env vars) will still apply.
    pass

# Ensure DEEPSEEK_API_KEY is set in your environment
if "DEEPSEEK_API_KEY" not in os.environ:
    st.warning("Set environment variable DEEPSEEK_API_KEY before running. Example: export DEEPSEEK_API_KEY='sk-...'")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Difficulty / complexity tuning
CORRECT_SCORE_THRESHOLD = 16  # score >= this is considered a correct/good answer
MAX_COMPLEXITY = 5
MIN_COMPLEXITY = 1

# Initialize LLM via LangChain with DeepSeek
client = httpx.Client(verify=False)
llm = ChatOpenAI(
base_url="https://genailab.tcs.in",
model = "azure_ai/genailab-maas-DeepSeek-V3-0324",
api_key="sk-DoW1qrOmGHAothEoYV2oSA",
http_client = client
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
    if "complexity_level" not in st.session_state:
        st.session_state.complexity_level = 1

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


def text_to_speech(text: str) -> str:
    """Return a small JS snippet to speak text using SpeechSynthesis."""
    import json as _json
    safe_text = _json.dumps(text)
    js = f"""
    <script>
    (function() {{
        try {{
            var msg = new SpeechSynthesisUtterance();
            msg.text = {safe_text};
            msg.lang = 'en-US';
            msg.rate = 0.9;
            msg.pitch = 1;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(msg);
        }} catch(e) {{ console.warn('TTS error', e); }}
    }})();
    </script>
    """
    return js


def create_audio_player(text: str, key: str) -> str:
    """Return minimal HTML/JS for a TTS button that works across browsers."""
    import json as _json
    safe_text = _json.dumps(text)
    html = f"""
    <div id="tts_container_{key}">
      <button id="btn_{key}" style="background:#667eea;color:#fff;border:none;padding:8px 14px;border-radius:8px;">🔊 Listen</button>
    </div>
    <script>
    (function() {{
        try {{
            var btn = document.getElementById('btn_{key}');
            function speak() {{
                try {{
                    var u = new SpeechSynthesisUtterance({safe_text});
                    u.lang = 'en-US'; u.rate = 0.9; u.pitch = 1.0;
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(u);
                }} catch(e) {{ console.warn('speak failed', e); }}
            }}
            if (btn) {{ btn.addEventListener('click', function(e){{ e.preventDefault(); speak(); }}); }}
        }} catch(e) {{ console.warn('create_audio_player error', e); }}
    }})();
    </script>
    """
    return html

def create_timer_html(start_time: float, max_seconds: int, key: str) -> str:
        """Return HTML+JS for a client-side countdown timer that updates every second.

        start_time: epoch seconds (float). If 0 or None, timer will show full time and count down from now.
        """
        # Ensure numeric values are passed into the JS
        st = float(start_time) if start_time else 0.0
        ms = int(max_seconds)
        safe_key = str(key)
        html = f"""
        <div id="timer_container_{safe_key}" style="text-align:center;padding:6px 8px;">
            <div id="timer_label_{safe_key}" style="font-size:12px;color:#666;margin-bottom:6px;">Question Timer</div>
            <div id="timer_value_{safe_key}" style="font-family:monospace; font-size:20px; font-weight:700;">--:--</div>
        </div>
        <script>
        (function() {{
            var start = {st};
            var maxSecs = {ms};
            var label = document.getElementById('timer_label_{safe_key}');
            var valueEl = document.getElementById('timer_value_{safe_key}');

            function fmt(s) {{
                var m = Math.floor(s/60); var sec = Math.floor(s%60);
                return (m<10?('0'+m):m) + ':' + (sec<10?('0'+sec):sec);
            }}

            var autoSubmitted = false;
            function tryAutoSubmit() {{
                try {{
                    // Use parent document when available (component runs inside an iframe)
                    var hostDoc = (window.parent && window.parent.document) ? window.parent.document : document;
                    // Find likely answer textarea(s) - prefer visible ones
                    var candidates = Array.from(hostDoc.querySelectorAll('textarea'));
                    var target = null;
                    for (var i=0;i<candidates.length;i++){{
                        var el = candidates[i];
                        try {{ if (el.offsetParent === null) continue; }} catch(e) {{ /* some nodes may not expose offsetParent cross-doc */ }}
                        var ph = (el.getAttribute('placeholder') || '').toLowerCase();
                        if (ph.includes('type your answer') || ph.includes('write your code') || (el.id && el.id.includes('answer'))) {{ target = el; break; }}
                    }}
                    if (!target && candidates.length>0) target = candidates[candidates.length-1];

                    var val = target ? (target.value || '').trim() : '';
                    // Find buttons - Streamlit renders form buttons as <button> elements; prefer visible ones
                    var buttons = Array.from(hostDoc.querySelectorAll('button'));
                    var submitBtn = null, skipBtn = null;
                    buttons.forEach(function(b){{
                        try {{
                            if (b.offsetParent === null) return; // hidden
                            var txt = (b.innerText || b.value || '').toLowerCase();
                            if (!submitBtn && (txt.includes('submit answer') || txt.includes('submit'))) submitBtn = b;
                            if (!skipBtn && (txt.includes('skip') || txt.includes("don't know") || txt.includes('dont know') || txt.includes("skip / don't know"))) skipBtn = b;
                        }} catch(e){{}}
                    }});

                    if (val && submitBtn) {{
                        console.log('[autosubmit] Answer present - auto-clicking Submit');
                        // Ensure Streamlit sees the latest value on the host document
                        try {{ target.dispatchEvent(new Event('input', {{ bubbles: true }})); }} catch(e) {{ console.warn('dispatch input failed', e); }}
                        try {{ submitBtn.click(); }} catch(e) {{ console.warn('submit click failed', e); }}
                        autoSubmitted = true;
                    }} else if (!val && skipBtn) {{
                        console.log('[autosubmit] No answer - auto-clicking Skip');
                        try {{ skipBtn.click(); }} catch(e) {{ console.warn('skip click failed', e); }}
                        autoSubmitted = true;
                    }} else {{
                        console.log('[autosubmit] Could not find target textarea or buttons to auto-submit.');
                    }}
                }} catch(e) {{ console.warn('auto-submit failed', e); }}
            }}

            function update() {{
                var now = Date.now()/1000;
                var elapsed = start && start>0 ? now - start : 0;
                var remaining = Math.max(0, Math.round(maxSecs - elapsed));
                var color = remaining>300 ? '#16a34a' : (remaining>60 ? '#d97706' : '#dc2626');
                var emoji = remaining>300 ? '🟢' : (remaining>60 ? '🟡' : '🔴');
                try {{
                    valueEl.textContent = fmt(remaining);
                    valueEl.style.color = color;
                    label.textContent = emoji + ' Question Timer';
                    // When timer reaches zero, attempt auto-submit once
                    if (remaining <= 0 && !autoSubmitted) {{
                        // Give a short delay to allow any pending user input events to settle
                        setTimeout(tryAutoSubmit, 250);
                    }}
                }} catch(e) {{ console.warn('timer update failed', e); }}
            }}

            update();
            setInterval(update, 1000);
        }})();
        </script>
        """
        return html

def create_total_timer_html(start_time: float, max_seconds: int, key: str) -> str:
    """Client-side total countdown timer that attempts to click a hidden auto-end button when expired."""
    st_val = float(start_time) if start_time else 0.0
    ms = int(max_seconds)
    safe_key = str(key)
    html = f"""
    <div id="total_timer_container_{safe_key}" style="text-align:center;padding:6px 8px;">
        <div id="total_timer_label_{safe_key}" style="font-size:12px;color:#666;margin-bottom:6px;">Total Interview Time</div>
        <div id="total_timer_value_{safe_key}" style="font-family:monospace; font-size:18px; font-weight:700;">--:--</div>
    </div>
    <script>
    (function() {{
        var start = {st_val};
        var maxSecs = {ms};
        var label = document.getElementById('total_timer_label_{safe_key}');
        var valueEl = document.getElementById('total_timer_value_{safe_key}');

        function fmt(s) {{
            var m = Math.floor(s/60); var sec = Math.floor(s%60);
            return (m<10?('0'+m):m) + ':' + (sec<10?('0'+sec):sec);
        }}

        var done = false;
        function tryAutoEnd() {{
            try {{
                var hostDoc = (window.parent && window.parent.document) ? window.parent.document : document;
                // Try to find a dedicated auto-end button by text
                var buttons = Array.from(hostDoc.querySelectorAll('button'));
                var target = null;
                buttons.forEach(function(b) {{
                    try {{
                        var txt = (b.innerText || b.value || '').toLowerCase();
                        if (!target && (txt.includes('auto end') || txt.includes('end interview') || txt.includes('finish interview') || txt.includes('export complete evaluation report') )) {{
                            target = b;
                        }}
                    }} catch(e){{}}
                }});

                if (target) {{
                    console.log('[total-autotimer] clicking auto-end target');
                    try {{ target.click(); }} catch(e) {{ console.warn('auto-end click failed', e); }}
                    done = true;
                }} else {{
                    // If no dedicated button, try to trigger a general rerun by clicking any visible interactive button (best-effort)
                    for (var i=0;i<buttons.length;i++) {{
                        try {{ if (buttons[i].offsetParent !== null) {{ buttons[i].click(); done = true; break; }} }} catch(e){{}}
                    }}
                    if (!done) console.log('[total-autotimer] no button found to click for auto-end');
                }}
            }} catch(e) {{ console.warn('tryAutoEnd failed', e); }}
        }}

        function update() {{
            var now = Date.now()/1000;
            var elapsed = start && start>0 ? now - start : 0;
            var remaining = Math.max(0, Math.round(maxSecs - elapsed));
            try {{
                valueEl.textContent = fmt(remaining);
                var color = remaining>600 ? '#16a34a' : (remaining>120 ? '#d97706' : '#dc2626');
                valueEl.style.color = color;
                if (remaining <= 0 && !done) {{
                    // Slight delay so any final events settle
                    setTimeout(tryAutoEnd, 250);
                }}
            }} catch(e) {{ console.warn('total timer update failed', e); }}
        }}

        update();
        setInterval(update, 1000);
    }})();
    </script>
    """
    return html

def create_code_ide_html(initial_code: str, key: str, language: str = 'python') -> str:
        """Return HTML for an embedded Ace editor with Save->Parent textarea functionality."""
        import json as _json
        safe_code = _json.dumps(initial_code)
        safe_key = str(key)

        # Template uses placeholders which we'll replace safely
        template = '''
        <div style="font-family:monospace;color:#fff">
            <div id="editor_%%SAFE_KEY%%" style="height:320px;width:100%;border-radius:8px;overflow:hidden;margin-bottom:8px;"></div>
            <div style="display:flex;gap:8px;">
                <button id="save_%%SAFE_KEY%%" style="background:linear-gradient(90deg,#10b981,#06b6d4);border:none;padding:8px 12px;border-radius:8px;color:#fff;font-weight:600;">Save to Answer</button>
                <button id="clear_%%SAFE_KEY%%" style="background:#374151;border:none;padding:8px 12px;border-radius:8px;color:#fff;font-weight:600;">Clear</button>
                <div id="ide_status_%%SAFE_KEY%%" style="margin-left:8px;color:#ddd;align-self:center;font-size:13px"></div>
            </div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.14/ace.js" crossorigin="anonymous"></script>
        <script>
        (function(){
            try {
                var editor = ace.edit('editor_' + %%SAFE_KEY_JSON%%);
                editor.setTheme('ace/theme/monokai');
                var lang = %%LANG_QUOTED%%;
                var mode = 'ace/mode/python';
                try {
                    if (lang === 'javascript') mode = 'ace/mode/javascript';
                    else if (lang === 'java') mode = 'ace/mode/java';
                    else if (lang === 'c' || lang === 'cpp') mode = 'ace/mode/c_cpp';
                    else if (lang === 'go') mode = 'ace/mode/golang';
                    else if (lang === 'ruby') mode = 'ace/mode/ruby';
                } catch(e) {}
                editor.session.setMode(mode);
                editor.session.setValue(%%SAFE_CODE%%);
                editor.session.setTabSize(4);

                function findAnswerTextarea() {
                    var hostDoc = (window.parent && window.parent.document) ? window.parent.document : document;
                    var candidates = Array.from(hostDoc.querySelectorAll('textarea'));
                    var target = null;
                    for (var i=0;i<candidates.length;i++){
                        var el = candidates[i];
                        try { if (el.offsetParent === null) continue; } catch(e){}
                        var ph = (el.getAttribute('placeholder')||'').toLowerCase();
                        if (ph.includes('write your code') || ph.includes('type your answer') || (el.id && el.id.includes('answer'))) { target = el; break; }
                    }
                    if (!target && candidates.length>0) target = candidates[candidates.length-1];
                    return target;
                }

                document.getElementById('save_' + %%SAFE_KEY_JSON%%).addEventListener('click', function(e){
                    e.preventDefault();
                    try{
                        var code = editor.getValue();
                        var tgt = findAnswerTextarea();
                        if (tgt) {
                            try {
                                // Use native setter to ensure React/Streamlit detects the change
                                var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                                if (setter) {
                                    setter.call(tgt, code);
                                } else {
                                    tgt.value = code;
                                }
                                // Dispatch input and change events so Streamlit picks up the new value
                                tgt.dispatchEvent(new Event('input', { bubbles: true }));
                                tgt.dispatchEvent(new Event('change', { bubbles: true }));
                                document.getElementById('ide_status_' + %%SAFE_KEY_JSON%%).textContent = 'Saved to answer field';
                            } catch(inner) {
                                console.warn('native set failed', inner);
                                try { tgt.value = code; tgt.dispatchEvent(new Event('input', { bubbles: true })); } catch(e2){}
                                document.getElementById('ide_status_' + %%SAFE_KEY_JSON%%).textContent = 'Saved (best-effort)';
                            }
                        } else {
                            document.getElementById('ide_status_' + %%SAFE_KEY_JSON%%).textContent = 'Could not find answer field on page';
                        }
                    } catch(err) { console.warn(err); document.getElementById('ide_status_' + %%SAFE_KEY_JSON%%).textContent = 'Save failed'; }
                });

                document.getElementById('clear_' + %%SAFE_KEY_JSON%%).addEventListener('click', function(e){
                    e.preventDefault(); editor.session.setValue(''); document.getElementById('ide_status_' + %%SAFE_KEY_JSON%%).textContent = 'Cleared';
                });
            } catch(e) { console.warn('IDE init failed', e); }
        })();
        </script>
        '''

        # Safe JSON-encoded key for JS concatenation (includes quotes)
        safe_key_json = _json.dumps(safe_key)
        # Quoted language string for JS comparison
        lang_quoted = _json.dumps(language)

        html = template.replace('%%SAFE_KEY%%', safe_key)
        html = html.replace('%%SAFE_KEY_JSON%%', safe_key_json)
        html = html.replace('%%SAFE_CODE%%', safe_code)
        html = html.replace('%%LANG_QUOTED%%', lang_quoted)

        return html

# Simple file-backed DB helpers
USERS_DB = "users.json"
EVAL_HISTORY_DB = "evaluation_history.json"

def load_users():
    if os.path.exists(USERS_DB):
        try:
            with open(USERS_DB, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_DB, 'w') as f:
        json.dump(users, f, indent=2)

def load_eval_history():
    if os.path.exists(EVAL_HISTORY_DB):
        try:
            with open(EVAL_HISTORY_DB, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_eval_history(history):
    with open(EVAL_HISTORY_DB, 'w') as f:
        json.dump(history, f, indent=2)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

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

def build_question_prompt(role: str, skills: List[str], language: str, is_coding: bool = False, asked_questions: List[str] = None, complexity: int = 1):
    # Template that asks the LLM to produce role-specific technical questions
    previous_questions = ""
    if asked_questions:
        # Escape any literal braces so PromptTemplate won't treat them as variables
        def _escape_braces(s: str) -> str:
            return s.replace('{', '{{').replace('}', '}}')

        prev_text = _escape_braces(', '.join(asked_questions))
        previous_questions = f"\n\nIMPORTANT: Do NOT repeat these previously asked questions: {prev_text}\nGenerate a completely DIFFERENT question."
    
    complexity_note = f"Make the question complexity level: {complexity} (1=easiest, {MAX_COMPLEXITY}=hardest)."
    if is_coding:
        template = (
            "You are an interview generator for the role of {role}. "
            "The candidate's listed skills: {skills}. "
            "Generate one UNIQUE coding problem or algorithm question that requires writing actual code. "
            "The question should ask the candidate to write a function, method, or code snippet. "
            f"{complexity_note} "
            "Make it practical and relevant to the role. "
            "Do not include answer or explanation. Output ONLY the question text. "
            f"Respond in {{language}}.{previous_questions}"
        )
    else:
        template = (
            "You are an interview generator for the role of {role}. "
            "The candidate's listed skills: {skills}. "
            "Generate one UNIQUE theoretical or conceptual technical question (not a behavioral question) that tests these skills. "
            f"{complexity_note} "
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

def gen_question(role: str, skills: List[str], language: str, question_num: int = 1, asked_questions: List[str] = None, complexity: int = 1) -> tuple:
    # Questions 3 and 5 will be coding questions
    is_coding = question_num in [3, 5]
    prompt = build_question_prompt(role, ", ".join(skills), language, is_coding, asked_questions, complexity)
    
    # Use temperature > 0 for variety in questions
    varied_llm = ChatOpenAI(
        base_url="https://genailab.tcs.in",
        model = "azure_ai/genailab-maas-DeepSeek-V3-0324",
        api_key="sk-DoW1qrOmGHAothEoYV2oSA",
        http_client = client,
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

# Use a persistent selectbox value stored in session_state so the selection survives reruns.
if 'nav_choice' not in st.session_state:
    st.session_state.nav_choice = menu[0]

# If a page_redirect was requested, apply it to the persistent nav_choice and clear it.
if getattr(st.session_state, 'page_redirect', None) in menu:
    st.session_state.nav_choice = st.session_state.page_redirect
    st.session_state.page_redirect = None

# Render the selectbox with a stable key so the user's selection persists across reruns.
choice = st.sidebar.selectbox("📋 Navigation", menu, key='nav_choice')

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
            first_q, is_coding = gen_question(st.session_state.role, st.session_state.skills, st.session_state.lang, question_num=1, asked_questions=[], complexity=st.session_state.complexity_level)
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
                try:
                    # Client-side total timer that updates without Streamlit reruns
                    timer_html = create_total_timer_html(st.session_state.total_start_time or time.time(), 50 * 60, "total")
                    st.components.v1.html(timer_html, height=80, scrolling=False)
                except Exception:
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
            # Diagnostic Test TTS button
            if st.session_state.voice_mode:
                test_button_html = """
                <div style="display:flex; flex-direction:column; gap:8px;">
                                    <div>
                                        <button id="tts_test_btn" style="
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: 600;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    ">🔊 Test TTS</button>
                    <button id="tts_clear_btn" style="
                        background-color: #95a5a6;
                        color: white;
                        border: none;
                        padding: 8px 12px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 12px;
                        margin-left:8px;
                    ">🧹 Clear Log</button>
                  </div>
                  <div id="tts_diag_area" style="background:#fafafa;border:1px solid #e6e6e6;padding:6px;border-radius:6px;max-height:120px;overflow:auto;font-size:13px;">
                    <div id="voices_list">Voices: (not checked)</div>
                    <div id="tts_log" style="margin-top:8px;color:#222"></div>
                  </div>
                </div>
                <script type="text/javascript">
                function logTTS(msg) {
                    try {
                        var l = document.getElementById('tts_log');
                        var el = document.createElement('div');
                        el.textContent = (new Date()).toLocaleTimeString() + ' — ' + msg;
                        l.appendChild(el);
                        // keep scrolled to bottom
                        l.parentElement.scrollTop = l.parentElement.scrollHeight;
                    } catch(e) { console.log('logTTS error', e); }
                }

                function clearTTSLog() {
                    try { document.getElementById('tts_log').innerHTML = ''; document.getElementById('voices_list').innerHTML = 'Voices: (not checked)'; } catch(e){}
                }

                function renderVoices(vs) {
                    try {
                        var html = '<strong>Voices (' + (vs.length || 0) + '):</strong><ul style="margin:4px 0;padding-left:18px;">';
                        vs.forEach(function(v){ html += '<li>' + (v.name || 'unknown') + ' (' + (v.lang||'') + ')' + (v.default? ' [default]':'') + '</li>'; });
                        html += '</ul>';
                        document.getElementById('voices_list').innerHTML = html;
                    } catch(e){ console.warn('renderVoices error', e); }
                }

                function testTTS() {
                    logTTS('Starting diagnostic...');

                    if (!('speechSynthesis' in window)) {
                        logTTS('Speech Synthesis API not supported in this browser.');
                        alert('Speech synthesis is not supported in your browser');
                        return;
                    }

                    // Cancel any ongoing speech
                    try { window.speechSynthesis.cancel(); } catch(e) { console.warn(e); }

                    var speakNow = function(vs) {
                        try {
                            var msg = new SpeechSynthesisUtterance('This is a diagnostic test. If you hear this, text to speech is working.');
                            msg.lang = 'en-US';
                            msg.rate = 0.9;
                            msg.pitch = 1;
                            msg.volume = 1;

                            msg.onstart = function() { logTTS('TTS playback started'); };
                            msg.onend = function() { logTTS('TTS playback ended'); };
                            msg.onerror = function(ev) { logTTS('TTS playback error: ' + (ev && ev.error ? ev.error : JSON.stringify(ev))); alert('TTS Error: ' + (ev && ev.error ? ev.error : 'unknown')); };

                            // Choose a preferred English voice if available
                            var preferred = null;
                            try {
                                preferred = (vs || []).find(function(v){ return v && v.lang && v.lang.toLowerCase().startsWith('en'); }) || (vs && vs[0]);
                            } catch(e) { console.warn('voice pick error', e); }
                            if (preferred) {
                                try { msg.voice = preferred; logTTS('Using voice: ' + (preferred.name || preferred.lang)); } catch(e) { logTTS('Could not set voice: ' + e); }
                            } else {
                                logTTS('No voice chosen (empty list)');
                            }

                            // Speak after a short delay to ensure cancel took effect
                            setTimeout(function(){ try { window.speechSynthesis.speak(msg); } catch(e) { logTTS('Speak call failed: ' + e); } }, 120);
                        } catch(e) { logTTS('speakNow exception: ' + e); }
                    };

                    // If voices already available
                    var currentVoices = (window.speechSynthesis.getVoices && window.speechSynthesis.getVoices()) || [];
                    if (currentVoices.length > 0) {
                        renderVoices(currentVoices);
                        logTTS('Voices available: ' + currentVoices.length);
                        speakNow(currentVoices);
                        return;
                    }

                    // Wait for voiceschanged event (Edge/Chromium may load them asynchronously)
                    var appeared = false;
                    var onVoices = function() {
                        try {
                            var vs = window.speechSynthesis.getVoices() || [];
                            renderVoices(vs);
                            logTTS('voiceschanged event fired, voices: ' + vs.length);
                            if (!appeared) { appeared = true; speakNow(vs); }
                        } catch(e) { console.warn(e); }
                    };
                    try {
                        if (window.speechSynthesis.addEventListener) {
                            window.speechSynthesis.addEventListener('voiceschanged', onVoices);
                        } else {
                            window.speechSynthesis.onvoiceschanged = onVoices;
                        }
                        // Also attempt to trigger getVoices to populate list
                        setTimeout(function(){ try { renderVoices(window.speechSynthesis.getVoices() || []); logTTS('Requested voices list; waiting for voiceschanged...'); } catch(e){} }, 50);
                    } catch(e) { logTTS('Failed to attach voiceschanged listener: ' + e); }
                }
                // Attach event listeners to buttons to avoid inline onclicks
                try {
                    var _btn_test = document.getElementById('tts_test_btn');
                    if (_btn_test && !_btn_test._copilot_bound) { _btn_test.addEventListener('click', function(e){ e.preventDefault(); try{ testTTS(); }catch(err){ console.error(err); } }); _btn_test._copilot_bound = true; }
                    var _btn_clear = document.getElementById('tts_clear_btn');
                    if (_btn_clear && !_btn_clear._copilot_bound) { _btn_clear.addEventListener('click', function(e){ e.preventDefault(); try{ clearTTSLog(); }catch(err){ console.error(err); } }); _btn_clear._copilot_bound = true; }
                } catch(e) { console.warn('attach listeners failed', e); }
                </script>
                """
                # Use components.html so embedded <script> tags run (st.markdown sanitizes scripts)
                try:
                    st.components.v1.html(test_button_html, height=120, scrolling=True)
                except Exception:
                    # Fallback to markdown if components not available
                    st.markdown(test_button_html, unsafe_allow_html=True)
                st.caption("Click to run a diagnostic TTS test (shows voices and logs). If you see no voices, open DevTools Console for more details.")
        
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
                        # HTML-based TTS button — use components to allow scripts to run
                        try:
                            st.components.v1.html(create_audio_player(st.session_state.current_question, f"q{st.session_state.question_count}"), height=80, scrolling=False)
                        except Exception:
                            st.markdown(create_audio_player(st.session_state.current_question, f"q{st.session_state.question_count}"), unsafe_allow_html=True)
                    with col_tts2:
                        st.caption("💡 Click the button above to hear the question read aloud")
            
            with col2:
                # Use client-side timer so it updates automatically without Streamlit rerun
                try:
                    timer_html = create_timer_html(st.session_state.question_start_time or time.time(), 3 * 60, f"q{st.session_state.question_count}")
                    st.components.v1.html(timer_html, height=60, scrolling=False)
                except Exception:
                    # fallback to static metric
                    timer_color = "🟢" if question_time_remaining > 300 else "🟡" if question_time_remaining > 60 else "🔴"
                    st.metric(f"{timer_color} Question Timer", format_time(question_time_remaining))
            with col3:
                if st.button("🔄", help="Refresh timer"):
                    st.rerun()

        # Candidate answer input
        if not st.session_state.finalized:
            # Check if question time expired
            question_time_remaining = get_time_remaining(st.session_state.question_start_time, 10 * 60)
            
      
                
            
            with st.form("answer_form", clear_on_submit=True):
                # Pre-fill with audio transcription if available
                default_text = st.session_state.audio_answer if st.session_state.audio_answer else ""
                placeholder_text = "Write your code here..." if st.session_state.current_is_coding else "Type your answer here (or use voice input above)..."
                # If coding question, provide an embedded code IDE to write code
                if st.session_state.current_is_coding:
                    # Allow candidate to choose language for the coding IDE
                    lang_choice = st.selectbox("Code language", ["python", "javascript", "java", "c", "cpp", "go", "ruby"], index=0, key=f"lang_q{st.session_state.question_count}")
                    try:
                        st.components.v1.html(create_code_ide_html(default_text, f"ide_q{st.session_state.question_count}", language=lang_choice), height=420, scrolling=True)
                    except Exception:
                        # fallback to textarea if components not available
                        pass
                    answer = st.text_area("Your answer", value=default_text, key="answer_area", height=220, placeholder=placeholder_text)
                else:
                    answer = st.text_area("Your answer", value=default_text, key="answer_area", height=150, placeholder=placeholder_text)
                
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

                    # Adjust complexity based on result: increase complexity on good answers
                    try:
                        if score >= CORRECT_SCORE_THRESHOLD:
                            st.session_state.complexity_level = min(MAX_COMPLEXITY, st.session_state.complexity_level + 1)
                        else:
                            # keep same complexity on incorrect or low score
                            st.session_state.complexity_level = max(MIN_COMPLEXITY, st.session_state.complexity_level)
                    except Exception:
                        # ensure complexity stays within bounds
                        st.session_state.complexity_level = max(MIN_COMPLEXITY, min(MAX_COMPLEXITY, st.session_state.get('complexity_level', 1)))
                    
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
                                    asked_questions=st.session_state.asked_questions,
                                    complexity=st.session_state.complexity_level
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
