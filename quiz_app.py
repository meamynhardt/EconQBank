import streamlit as st
import pandas as pd
import os
from fpdf import FPDF

# Set page configuration
st.set_page_config(page_title="Economics QBank Quiz", layout="wide")

# 1. Load Data: 'utf-8-sig' handles Excel/Windows CSVs better than latin-1
@st.cache_data
def load_data():
    return pd.read_csv("Economics QBank - Qbank.csv", encoding='utf-8-sig')

df = load_data()

# 2. PDF Generator
def generate_pdf(filtered_df):
    pdf = FPDF()
    pdf.add_page()
    
    def clean(text):
        text = str(text)
        # Standardize quotes and dashes to prevent encoding crashes
        replacements = {'“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-'}
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Economics Quiz (Selected Questions)", ln=True, align='C')
    pdf.ln(10)
    
    for count, (index, row) in enumerate(filtered_df.iterrows(), 1):
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 8, txt=f"{count}. {clean(row['Question'])}")
        
        for col in ['Image', 'Image_1']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                path = str(row[col]).strip()
                if os.path.exists(path):
                    pdf.image(path, w=100)
                    pdf.ln(2)
        
        if pd.notna(row['Options']):
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, txt=clean(row['Options']))
        pdf.ln(8)
    return pdf.output(dest='S').encode('latin-1')

# 3. Sidebar Filters
st.sidebar.header("Quiz Settings")
levels = sorted(df['Level'].dropna().unique().tolist())
difficulties = sorted(df['Difficulty'].dropna().unique().tolist())
topics = sorted(df['Topic'].dropna().unique().tolist())
objectives = sorted(df['Objective'].dropna().unique().tolist())

selected_level = st.sidebar.selectbox("Select Level", ["All"] + levels)
selected_difficulty = st.sidebar.selectbox("Select Difficulty", ["All"] + difficulties)
selected_topic = st.sidebar.selectbox("Select Topic", ["All"] + topics)
selected_objective = st.sidebar.selectbox("Select Objective", ["All"] + objectives)

filtered_df = df.copy()
if selected_level != "All": filtered_df = filtered_df[filtered_df['Level'] == selected_level]
if selected_difficulty != "All": filtered_df = filtered_df[filtered_df['Difficulty'] == selected_difficulty]
if selected_topic != "All": filtered_df = filtered_df[filtered_df['Topic'] == selected_topic]
if selected_objective != "All": filtered_df = filtered_df[filtered_df['Objective'] == selected_objective]

# 4. Session State
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'answered' not in st.session_state: st.session_state.answered = False

# Reset if filters change
if st.sidebar.button("Apply Filters"):
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.rerun()

# 5. Main UI
st.title("Economics Quiz Generator")

if len(filtered_df) == 0:
    st.warning("No questions match these filters.")
else:
    # --- VISUAL TALLY ---
    total_q = len(filtered_df)
    current_q_num = st.session_state.idx + 1
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Question {current_q_num} of {total_q}")
    with col2:
        st.metric("Score", f"{st.session_state.score} / {st.session_state.idx}")
    
    st.markdown("---")
    
    row = filtered_df.iloc[st.session_state.idx]
    st.write(f"**{str(row['Question']).strip()}**")
    
    for col in ['Image', 'Image_1']:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            path = str(row[col]).strip()
            if os.path.exists(path): st.image(path)
            else: st.error(f"Image not found at: {path}")

    opts = str(row['Options']).split('\n')
    choice = st.radio("Select Answer:", opts, index=None)
    
    if st.button("Submit"):
        if choice and choice.startswith(str(row['Answer']).strip()):
            st.success("Correct!")
            st.session_state.score += 1
        else:
            st.error(f"Incorrect. Correct answer: {row['Answer']}")
        st.session_state.answered = True
        st.rerun()

    if st.session_state.answered and st.button("Next"):
        st.session_state.idx = (st.session_state.idx + 1) % total_q
        st.session_state.answered = False
        st.rerun()

    st.sidebar.download_button("Download PDF", generate_pdf(filtered_df), "quiz.pdf", "application/pdf")