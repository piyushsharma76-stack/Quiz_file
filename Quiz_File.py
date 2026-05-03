import streamlit as st
import pandas as pd
import time
import os

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Sahayaks Quiz", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 5rem !important; }
    .stApp { background-color: #0F1937; color: #FFFFFF; }

    .stat-box { 
        font-size: 26px !important; 
        font-weight: bold; 
        text-align: center; 
        background-color: #1E2A4A;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #3E4A6A;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: white;
    }

    .stButton>button {
        background-color: #1E2A4A; color: white; border-radius: 10px;
        height: 4em; width: 100%; font-size: 20px; font-weight: bold;
        margin-bottom: 12px;
        border: 2px solid #3E4A6A;
    }

    .feedback-text { font-size: 32px; font-weight: bold; text-align: center; margin-top: 25px; }
    .ans-box { 
        background-color: #26355d; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #FFD700;
        margin-bottom: 10px;
        color: white;
    }
    .expl-box { 
        background-color: #1b2641; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #00aaff;
        color: #e0e0e0;
        line-height: 1.6;
    }
    .countdown-text { font-size: 22px; color: #FFD700; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


# --- 2. AUDIO FEEDBACK HELPER ---
def play_sound(sound_type):
    url = "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" if sound_type == "success" else "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    st.components.v1.html(f"""
        <audio autoplay><source src="{url}" type="audio/mpeg"></audio>
    """, height=0)


# --- 3. DATA LOADING ---
@st.cache_data(show_spinner="Updating Quiz Data...")
def load_data():
    file_path = "Questions1.xlsx"
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns]
        # Remove duplicates to ensure unique question sets
        return df.drop_duplicates(subset=['Question']).dropna(subset=['Question'])
    except Exception as e:
        st.error(f"Error loading file. Details: {e}")
        return pd.DataFrame()


if st.sidebar.button("🔄 Force Reload File"):
    st.cache_data.clear()
    st.rerun()

df_all = load_data()

# --- 4. CHAPTER SELECTION ---
selected_chapter = st.query_params.get("chapter")

if not selected_chapter:
    st.markdown("<h1 style='text-align: center; color: #FFD700; margin-bottom: 50px;'>Select a Chapter to Begin</h1>",
                unsafe_allow_html=True)
    if not df_all.empty:
        chapters = sorted(df_all['Chapter'].unique())
        cols = st.columns(3)
        for idx, ch in enumerate(chapters):
            with cols[idx % 3]:
                if st.button(f"📘 {ch}", key=f"ch_{idx}"):
                    st.query_params["chapter"] = ch
                    st.rerun()
    st.stop()

# --- 5. DATA FILTERING ---
questions = df_all[df_all['Chapter'] == selected_chapter].to_dict('records')
TOTAL_Q = len(questions)

# --- 6. STATE MANAGEMENT ---
state_key = f"quiz_{selected_chapter}"
if state_key not in st.session_state:
    st.session_state[state_key] = {
        'current_idx': 0,
        'score': 0,
        'quiz_over': False,
        'answered': False,
        'start_time': time.time(),
        'feedback_msg': "",
        'feedback_type': ""
    }

qs = st.session_state[state_key]

# --- 7. UI HEADER & TIMER ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='stat-box' style='color:#FFD700;'>🏆 Score: {qs['score']}</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='stat-box'>Q: {qs['current_idx'] + 1} / {TOTAL_Q}</div>", unsafe_allow_html=True)
with col3:
    timer_placeholder = st.empty()

st.markdown("<br><br>", unsafe_allow_html=True)

# --- 8. TIMER LOGIC (15s per question) ---
if not qs['quiz_over'] and not qs['answered']:
    elapsed = time.time() - qs['start_time']
    time_left = max(0, int(15 - elapsed))
    timer_placeholder.markdown(f"<div class='stat-box' style='color:#FF4B4B;'>⏳ {time_left}s</div>",
                               unsafe_allow_html=True)

    if time_left <= 0:
        qs['answered'] = True
        qs['feedback_msg'] = "Time is Up! ⌛"
        qs['feedback_type'] = "error"
        play_sound("sorrow")
        st.rerun()
else:
    timer_placeholder.markdown(f"<div class='stat-box' style='color:#FF4B4B;'>⏳ 0s</div>", unsafe_allow_html=True)

# --- 9. QUIZ LOGIC ---
if not qs['quiz_over'] and qs['current_idx'] < TOTAL_Q:
    q_data = questions[qs['current_idx']]

    # Using a container to encapsulate the entire question/feedback area
    quiz_container = st.empty()

    if not qs['answered']:
        with quiz_container.container():
            st.markdown(f"<h2 style='text-align: center; line-height: 1.5; color: white;'>{q_data['Question']}</h2>",
                        unsafe_allow_html=True)
            btn_cols = st.columns([1, 2, 2, 1])


            def select_answer(option_text):
                qs['answered'] = True
                if str(option_text).strip() == str(q_data['Correct Answer']).strip():
                    qs['score'] += 1
                    qs['feedback_msg'], qs['feedback_type'] = "Correct Answer! 🎺", "success"
                    play_sound("success")
                else:
                    qs['feedback_msg'], qs['feedback_type'] = "Incorrect Answer! ❌", "error"
                    play_sound("sorrow")
                st.rerun()


            with btn_cols[1]:
                if st.button(f"A. {q_data['Option1']}", key=f"A_{qs['current_idx']}"): select_answer(q_data['Option1'])
                if st.button(f"C. {q_data['Option3']}", key=f"C_{qs['current_idx']}"): select_answer(q_data['Option3'])
            with btn_cols[2]:
                if st.button(f"B. {q_data['Option2']}", key=f"B_{qs['current_idx']}"): select_answer(q_data['Option2'])
                if st.button(f"D. {q_data['Option4']}", key=f"D_{qs['current_idx']}"): select_answer(q_data['Option4'])

        # Trigger frequent reruns to keep the timer ticking
        time.sleep(1)
        st.rerun()

    else:
        # --- FEEDBACK PHASE (10 Seconds) ---
        with quiz_container.container():
            st.markdown(f"<h2 style='text-align: center; line-height: 1.5; color: white;'>{q_data['Question']}</h2>",
                        unsafe_allow_html=True)
            feedback_color = "#00FF00" if qs['feedback_type'] == "success" else "#FF4B4B"
            st.markdown(f"<div class='feedback-text' style='color:{feedback_color};'>{qs['feedback_msg']}</div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='ans-box'><b>Correct Answer:</b> {q_data['Correct Answer']}</div>",
                        unsafe_allow_html=True)

            expl = q_data.get('Explaination of Correct Answer', 'N/A')
            st.markdown(f"<div class='expl-box'><b>Explanation:</b> {expl}</div>", unsafe_allow_html=True)

            countdown_placeholder = st.empty()
            for i in range(10, 0, -1):
                countdown_placeholder.markdown(f"<p class='countdown-text'>Next question in {i} seconds...</p>",
                                               unsafe_allow_html=True)
                time.sleep(1)

            # CLEANUP AND ADVANCE
            # We clear the container and reset ALL feedback-related states before rerunning
            quiz_container.empty()
            qs['answered'] = False
            qs['feedback_msg'] = ""
            qs['feedback_type'] = ""
            qs['current_idx'] += 1
            qs['start_time'] = time.time()

            if qs['current_idx'] >= TOTAL_Q:
                qs['quiz_over'] = True
            st.rerun()

else:
    st.balloons()
    st.markdown("<h1 style='text-align: center; margin-top: 50px; color: white;'>🎉 Quiz Completed! 🎉</h1>",
                unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: #FFD700;'>Final Score: {qs['score']} / {TOTAL_Q}</h2>",
                unsafe_allow_html=True)

    if st.button("Restart Quiz"):
        del st.session_state[state_key]
        st.rerun()
