import os
import random
from io import BytesIO
import zipfile

import streamlit as st
import openai
from fpdf import FPDF

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("OpenAI API key not found! Please set the OPENAI_API_KEY environment variable.")

# ------------------------------------------------------------------
# Function: simulate GAN refinement via a second prompt
# ------------------------------------------------------------------
def refine_solution_with_gan(raw_text: str) -> str:
    refinement_prompt = (
        "You are an expert in refining student exam answers to sound more natural and human-like. "
        "Review the following raw answer and adjust it by adding natural language cues, slight imperfections, "
        "and a conversational tone (while keeping it clear and relevant):\n\n"
        f"{raw_text}\n\n"
        "Now, provide a refined version of this answer."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # or use "gpt-4" if preferred
            messages=[
                {"role": "system", "content": "You are a language refinement expert."},
                {"role": "user", "content": refinement_prompt}
            ],
            temperature=0.6,
            max_tokens=1000,
        )
        refined_text = response.choices[0].message.content.strip()
    except Exception as e:
        refined_text = raw_text + f"\n\n[Refinement error: {str(e)}]"
    return refined_text

# ------------------------------------------------------------------
# Function: generate a raw student solution using GPT-4 (updated syntax)
# then refine it to simulate a GAN-style output.
# ------------------------------------------------------------------
def generate_solution(questions: list, performance: str, student_number: int) -> str:
    prompt = (
        "You are a student taking an exam. The following are exam questions:\n" +
        "".join([f"\nQuestion {i+1}: {q}" for i, q in enumerate(questions)]) +
        "\n\n"
        f"Your performance level is \"{performance}\". Answer accordingly:\n"
        "- For \"excellent\": provide a detailed, well-structured answer.\n"
        "- For \"average\": provide a mostly correct answer with minor omissions.\n"
        "- For \"poor\": provide an answer that is brief and shows misunderstandings.\n\n"
        "Generate a realistic student solution as if written during an exam."
    )
    try:
        raw_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a student answering exam questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        raw_solution = raw_response.choices[0].message.content.strip()
    except Exception as e:
        raw_solution = f"Error generating solution: {str(e)}"
    
    refined_solution = refine_solution_with_gan(raw_solution)
    final_solution = f"Student {student_number} - Performance: {performance.upper()}\n\n" + refined_solution
    return final_solution

# ------------------------------------------------------------------
# Streamlit Application Layout
# ------------------------------------------------------------------
st.title("AI-Generated Dummy Solutions with GAN Simulation")

st.write(
    "Upload a sample question paper (TXT or PDF) to generate dummy student solutions. "
    "Each solution is generated using GPT-4 (with updated API syntax) and then refined via a second prompt "
    "to mimic human-like variations. You can choose how many solutions to generate."
)

# Allow user to input the number of solutions to generate.
num_solutions = st.number_input("Number of solutions to generate", min_value=1, max_value=100, value=20, step=1)

# File uploader: accepts TXT or PDF files.
uploaded_file = st.file_uploader("Upload Question Paper", type=["txt", "pdf"])

if uploaded_file is not None:
    file_text = ""
    if uploaded_file.type == "text/plain":
        file_text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            st.error("PyPDF2 is required to extract text from PDF files. Please install it with 'pip install PyPDF2'.")
        else:
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    file_text += extracted + "\n"
    
    if not file_text:
        st.error("Could not extract text from the uploaded file.")
    else:
        st.subheader("Question Paper Content:")
        st.text(file_text)
        
        # Parse questions: lines ending with '?' are considered as questions.
        questions = [line.strip() for line in file_text.split("\n") if line.strip().endswith("?")]
        if not questions:
            questions = [file_text.strip()]
        st.write(f"Identified {len(questions)} question(s) in the uploaded paper.")
        
        if st.button("Generate Dummy Solutions"):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(1, num_solutions + 1):
                    # Randomly assign a performance level.
                    performance = random.choices(
                        ["excellent", "average", "poor"],
                        weights=[0.2, 0.6, 0.2]
                    )[0]
                    
                    # Generate and refine the solution.
                    solution_text = generate_solution(questions, performance, i)
                    
                    # Create a PDF for the solution.
                    pdf = FPDF()
                    pdf.unifontsubset = False  # Fix: define the attribute to avoid AttributeError
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)  # Ensure current_font is set
                    for line in solution_text.split("\n"):
                        safe_line = line.encode("latin1", "replace").decode("latin1")
                        pdf.multi_cell(0, 10, txt=safe_line)
                    
                    pdf_data = pdf.output(dest="S").encode("latin1")
                    pdf_filename = f"dummy_solution_student_{i}.pdf"
                    zip_file.writestr(pdf_filename, pdf_data)
            
            zip_buffer.seek(0)
            st.success("Dummy solutions generated successfully!")
            st.download_button(
                "Download Dummy Solutions (ZIP)",
                data=zip_buffer,
                file_name="dummy_solutions.zip",
                mime="application/zip"
            )
