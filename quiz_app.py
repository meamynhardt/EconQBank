import streamlit as st
import pandas as pd
import os
from fpdf import FPDF

# Set page configuration
st.set_page_config(page_title="Economics QBank Quiz", layout="wide")

# 1. Load the database
@st.cache_data
def load_data():
    # 'latin-1' handles special characters that usually cause this error
    return pd.read_csv("Economics QBank - Qbank.csv", encoding='latin-1')
df = load_data()

# 2. PDF Generation Function
# 2. PDF Generation Function
def generate_pdf(filtered_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Economics Quiz", ln=True, align='C')
    pdf.ln(10)
    
    for count, (index, row) in enumerate(filtered_df.iterrows(), 1):
        def clean(text):
            return str(text).encode('latin-1', 'replace').decode('latin-1')
        
        # 1. Print Question
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 8, txt=f"{count}. {clean(row['Question'])}")
        pdf.ln(2)
        
        # 2. Insert First Image (if it exists)
        img_path_1 = str(row['Image']).strip()
        if img_path_1 and img_path_1.lower() != 'nan':
            if os.path.exists(img_path_1):
                try:
                    # w=130 keeps the image from going off the edge of an A4 page
                    pdf.image(img_path_1, w=130) 
                    pdf.ln(4)
                except Exception as e:
                    pdf.set_font("Arial", 'I', 10)
                    pdf.multi_cell(0, 6, txt="[Error: Image format not supported by PDF]")
        
        # 3. Insert Second Image (if it exists)
        if 'Image_1' in row:
            img_path_2 = str(row['Image_1']).strip()
            if img_path_2 and img_path_2.lower() != 'nan':
                if os.path.exists(img_path_2):
                    try:
                        pdf.image(img_path_2, w=130)
                        pdf.ln(4)
                    except Exception as e:
                        pdf.set_font("Arial", 'I', 10)
                        pdf.multi_cell(0, 6, txt="[Error: Second image format not supported]")
        
        # 4. Print Options
        if pd.notna(row['Options']):
            pdf.set_font("Arial", '', 11)
            for opt in str(row['Options']).split('\n'):
                if opt.strip():
                    pdf.multi_cell(0, 6, txt=clean(opt.strip()))
                    
        # Add space before the next question
        pdf.ln(8)
        
    return pdf.output(dest='S').encode('latin-1')

# 3. Sidebar Filters
st.sidebar.header("Quiz Settings")

levels = df['Level'].dropna().unique().tolist()
difficulties = df['Difficulty'].dropna().unique().tolist()
# Sort the list alphabetically
topics = sorted(df['Topic'].dropna().unique().tolist())
objectives = df['Objective'].dropna().unique().tolist()

selected_level = st.sidebar.selectbox("Select Level", ["All"] + levels)
selected_difficulty = st.sidebar.selectbox("Select Difficulty", ["All"] + difficulties)
selected_topic = st.sidebar.selectbox("Select Topic", ["All"] + topics)
selected_objective = st.sidebar.selectbox("Select Objective", ["All"] + objectives)

# Apply filters
filtered_df = df.copy()
if selected_level != "All":
    filtered_df = filtered_df[filtered_df['Level'] == selected_level]
if selected_difficulty != "All":
    filtered_df = filtered_df[filtered_df['Difficulty'] == selected_difficulty]
if selected_topic != "All":
    filtered_df = filtered_df[filtered_df['Topic'] == selected_topic]
if selected_objective != "All":
    filtered_df = filtered_df[filtered_df['Objective'] == selected_objective]

# Reset quiz if filters change
if 'previous_filters' not in st.session_state:
    st.session_state.previous_filters = (selected_level, selected_difficulty, selected_topic, selected_objective)

current_filters = (selected_level, selected_difficulty, selected_topic, selected_objective)
if current_filters != st.session_state.previous_filters:
    st.session_state.previous_filters = current_filters
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False

st.sidebar.markdown("---")
st.sidebar.write(f"**Available Questions:** {len(filtered_df)}")

# PDF Download Button
if len(filtered_df) > 0:
    st.sidebar.markdown("### Export")
    pdf_bytes = generate_pdf(filtered_df)
    st.sidebar.download_button(
        label="📄 Download Selected as PDF",
        data=pdf_bytes,
        file_name="custom_economics_quiz.pdf",
        mime="application/pdf"
    )

# 4. Initialize Session States for Quiz Tracking
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'answered' not in st.session_state:
    st.session_state.answered = False

# 5. Main UI
st.title("Economics Quiz Generator")

if len(filtered_df) == 0:
    st.warning("No questions match your current filters. Please adjust them in the sidebar.")
else:
    row = filtered_df.iloc[st.session_state.current_q_index]
    
    total_q = len(filtered_df)
    current_q_num = st.session_state.current_q_index + 1
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Question {current_q_num} of {total_q}")
    with col2:
        st.metric(label="Score", value=f"{st.session_state.score} / {st.session_state.current_q_index}")
        
    st.markdown("---")
    
    st.caption(f"Paper: {row['Paper']} | Topic: {row['Topic']} | Difficulty: {row['Difficulty']}")
    
    st.write(f"**{str(row['Question']).strip()}**")
    
    # --- FIRST IMAGE HANDLING LOGIC ---
    img_path_1 = str(row['Image']).strip()
    if img_path_1 and img_path_1.lower() != 'nan':
        if os.path.exists(img_path_1):
            st.image(img_path_1, caption="Diagram 1")
        else:
            st.error(f"Image not found at: {img_path_1}")
            
    # --- SECOND IMAGE HANDLING LOGIC ---
    if 'Image_1' in row:
        img_path_2 = str(row['Image_1']).strip()
        if img_path_2 and img_path_2.lower() != 'nan':
            if os.path.exists(img_path_2):
                st.image(img_path_2, caption="Diagram 2")
            else:
                st.error(f"Second image not found at: {img_path_2}")
    # -----------------------------------
    
    raw_options = str(row['Options'])
    if pd.notna(row['Options']):
        options_list = [opt.strip() for opt in raw_options.split('\n') if opt.strip() != ""]
    else:
        options_list = ["A", "B", "C", "D"]
        
    with st.form(key='quiz_form'):
        user_choice = st.radio("Select your answer:", options_list, index=None)
        submit_btn = st.form_submit_button("Submit Answer")
        
        if submit_btn:
            if user_choice is None:
                st.error("Please select an option before submitting.")
            else:
                st.session_state.answered = True
                correct_answer = str(row['Answer']).strip()
                
                if user_choice.startswith(correct_answer):
                    st.success(f"Correct! The answer is {correct_answer}.")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer was {correct_answer}.")

    if st.session_state.answered:
        if current_q_num < total_q:
            if st.button("Next Question"):
                st.session_state.current_q_index += 1  # Make sure this says current_q_index!
                st.session_state.answered = False
                st.rerun()
        else:
            st.info(f"Quiz Complete! Your final score is {st.session_state.score} out of {total_q}.")
            if st.button("Restart Quiz"):
                st.session_state.current_q_index = 0
                st.session_state.score = 0
                st.session_state.answered = False
                st.rerun()