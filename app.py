import streamlit as st
from file_processing import FileProcessor
from grading_engine import GradingEngine
import pandas as pd
import plotly.express as px
from pathlib import Path
import json

def initialize_session_state():
    if "grading_results" not in st.session_state:
        st.session_state.grading_results = []
    if "current_file_text" not in st.session_state:
        st.session_state.current_file_text = ""

def main():
    st.title("AI-Powered Assignment Grading System")
    
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter OpenAI API key", type="password")
        
        st.header("Grading Rubric")
        rubric = st.text_area(
            "Enter grading criteria",
            help="Specify the grading criteria for evaluating answers"
        )
        
        max_score = st.number_input("Maximum score per question", min_value=1, value=10)

    # Main content area
    uploaded_file = st.file_uploader("Upload assignment file (PDF/DOC/DOCX)", 
                                   type=['pdf', 'doc', 'docx'])

    if uploaded_file and api_key and rubric:
        try:
            processor = FileProcessor()
            file_text = processor.process_file(uploaded_file)
            
            if file_text != st.session_state.current_file_text:
                st.session_state.current_file_text = file_text
                
                # Display extracted text for verification
                with st.expander("View extracted text"):
                    st.text(file_text)
                
                # Process the text into Q&A pairs
                qa_pairs = processor.extract_qa_pairs(file_text)
                
                grading_engine = GradingEngine(api_key)
                
                # Grade each answer
                results = []
                progress_bar = st.progress(0)
                
                for i, (question, answer) in enumerate(qa_pairs):
                    with st.spinner(f'Grading question {i+1}/{len(qa_pairs)}...'):
                        result = grading_engine.grade_answer(
                            question=question,
                            answer=answer,
                            rubric=rubric,
                            max_score=max_score
                        )
                        results.append(result)
                        progress_bar.progress((i + 1) / len(qa_pairs))
                
                st.session_state.grading_results = results
                
            # Display results
            if st.session_state.grading_results:
                display_results(st.session_state.grading_results)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def display_results(results):
    st.header("Grading Results")
    
    # Calculate statistics
    scores = [result['score'] for result in results]
    avg_score = sum(scores) / len(scores)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Score", f"{avg_score:.2f}")
    with col2:
        st.metric("Total Questions", len(results))
    
    # Create a DataFrame for the results
    df = pd.DataFrame(results)
    
    # Plot score distribution
    fig = px.histogram(df, x='score', 
                      title='Score Distribution',
                      labels={'score': 'Score', 'count': 'Number of Questions'})
    st.plotly_chart(fig)
    
    # Display individual results with manual override capability
    for i, result in enumerate(results):
        with st.expander(f"Question {i+1} - Score: {result['score']}"):
            st.write("**Question:**", result['question'])
            st.write("**Answer:**", result['answer'])
            st.write("**Feedback:**", result['feedback'])
            
            # Manual override
            new_score = st.number_input(
                "Override score",
                min_value=0.0,
                max_value=10.0,
                value=float(result['score']),
                key=f"override_{i}"
            )
            new_feedback = st.text_area(
                "Override feedback",
                value=result['feedback'],
                key=f"feedback_{i}"
            )
            
            if st.button("Update", key=f"update_{i}"):
                st.session_state.grading_results[i]['score'] = new_score
                st.session_state.grading_results[i]['feedback'] = new_feedback
                st.success("Updated successfully!")
    
    # Export results
    if st.button("Download Results"):
        export_results(results)

def export_results(results):
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save to CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="grading_results.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main() 