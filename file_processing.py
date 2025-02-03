import PyPDF2
import docx
from io import BytesIO
import re

class FileProcessor:
    def process_file(self, uploaded_file):
        """Process uploaded file and extract text based on file type."""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self._extract_text_from_pdf(uploaded_file)
        elif file_extension in ['doc', 'docx']:
            return self._extract_text_from_doc(uploaded_file)
        else:
            raise ValueError("Unsupported file format")

    def _extract_text_from_pdf(self, file):
        """Extract text from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing PDF file: {str(e)}")

    def _extract_text_from_doc(self, file):
        """Extract text from DOC/DOCX file."""
        try:
            doc = docx.Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing DOC file: {str(e)}")

    def extract_qa_pairs(self, text):
        """
        Extract question-answer pairs from text.
        Assumes questions start with Q: or Question: and answers with A: or Answer:
        """
        # Split text into lines
        lines = text.split('\n')
        qa_pairs = []
        current_question = ""
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for question
            if line.lower().startswith(('q:', 'question:')):
                # If we have a previous Q&A pair, save it
                if current_question and current_answer:
                    qa_pairs.append((current_question, current_answer))
                
                # Start new question
                current_question = line.split(':', 1)[1].strip()
                current_answer = ""
                
            # Check for answer
            elif line.lower().startswith(('a:', 'answer:')):
                current_answer = line.split(':', 1)[1].strip()
            
            # Append to current answer if we're in answer section
            elif current_question and current_answer:
                current_answer += " " + line
        
        # Add the last Q&A pair
        if current_question and current_answer:
            qa_pairs.append((current_question, current_answer))
        
        return qa_pairs 