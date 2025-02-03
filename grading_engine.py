import openai
from typing import Dict, Any

class GradingEngine:
    def __init__(self, api_key: str):
        """Initialize the grading engine with OpenAI API key."""
        openai.api_key = api_key

    def grade_answer(self, question: str, answer: str, rubric: str, max_score: int = 10) -> Dict[str, Any]:
        """
        Grade a single answer using the OpenAI API.
        Returns a dictionary containing the score and feedback.
        """
        try:
            prompt = self._construct_prompt(question, answer, rubric, max_score)
            response = self._call_openai_api(prompt)
            
            # Parse the response
            result = self._parse_response(response)
            
            return {
                'question': question,
                'answer': answer,
                'score': result['score'],
                'feedback': result['feedback']
            }
            
        except Exception as e:
            raise Exception(f"Error during grading: {str(e)}")

    def _construct_prompt(self, question: str, answer: str, rubric: str, max_score: int) -> str:
        """Construct the prompt for the OpenAI API."""
        return f"""Please grade the following student answer based on the provided rubric:

Question: {question}

Student Answer: {answer}

Grading Rubric: {rubric}

Maximum Score: {max_score}

Please provide your response in the following format:
Score: [numerical score out of {max_score}]
Feedback: [detailed feedback explaining the grade and suggestions for improvement]

Please ensure your response maintains this exact format."""

    def _call_openai_api(self, prompt: str) -> str:
        """Make the API call to OpenAI."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an experienced teacher grading student assignments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the API response to extract score and feedback."""
        try:
            lines = response.split('\n')
            score = None
            feedback = []
            
            for line in lines:
                if line.lower().startswith('score:'):
                    score_text = line.split(':', 1)[1].strip()
                    # Extract the first number from the score text
                    score = float(next(filter(str.isdigit, score_text.replace('.', ''))))
                elif line.lower().startswith('feedback:'):
                    feedback.append(line.split(':', 1)[1].strip())
                elif feedback:  # Append additional feedback lines
                    feedback.append(line.strip())
            
            if score is None:
                raise ValueError("Could not parse score from response")
                
            return {
                'score': score,
                'feedback': ' '.join(feedback)
            }
            
        except Exception as e:
            raise Exception(f"Error parsing API response: {str(e)}") 