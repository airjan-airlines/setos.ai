import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("gemini_key") or os.getenv("GOOGLE_API_KEY")

jargon_prompt = """
You are a technical writing assistant specializing in making complex academic papers accessible to broader audiences. Your task is to analyze the provided abstract and create a comprehensive glossary of technical terms.
Instructions:
Step 1: Extract Direct Jargon

Identify all technical terms, acronyms, specialized vocabulary, and field-specific concepts mentioned in the abstract
Include mathematical notation, statistical measures, and methodological terms
Consider discipline-specific language that may not be familiar to readers outside the field

Step 2: Identify Implicit Prerequisites

Determine foundational concepts, theories, or background knowledge that readers would need to understand the abstract but aren't explicitly defined
Consider related terms or broader concepts that provide necessary context
Think about what a non-expert would need to know to grasp the significance of the work

Step 3: Provide Clear Explanations
For each term, provide:

Definition: A clear, concise explanation in plain language
Context: How the term relates to the specific research described
Significance: Why this concept matters for understanding the work (when relevant)
Related Terms: Connected concepts that help build understanding

Output Format:
Direct Terms from Abstract:
[Term 1]: [Clear definition and context]
[Term 2]: [Clear definition and context]
[Continue for all terms found in the abstract]
Essential Background Concepts:
[Concept 1]: [Definition and why it's important for understanding this work]
[Concept 2]: [Definition and why it's important for understanding this work]
[Continue for prerequisite knowledge]
Key Relationships:
Briefly explain how the main concepts connect to each other and to the overall research contribution.
 """

summarize_prompt = '''
You are a science communication expert who specializes in making complex research accessible to general audiences. Your task is to create an ultra-concise, plain-language summary of the provided technical abstract.
Instructions:
Create a 1-2 sentence TLDR (Too Long; Didn't Read) summary that:

Eliminates all jargon - Replace technical terms with everyday language
Focuses on the main finding or contribution - What did the researchers actually discover or achieve?
Explains the practical significance - Why should a general reader care about this?
Uses simple sentence structure - Avoid complex clauses and academic phrasing
Starts with action words when possible - "Researchers found..." "Scientists developed..." "This study shows..."

Target Audience:
Write for someone with a high school education who is curious about science but has no specialized knowledge in the field.
Output Format:
TLDR: [1-2 clear, jargon-free sentences explaining what was done and why it matters]
'''

instruction_dict = {"jargon" : jargon_prompt, "summary" : summarize_prompt}

def generate_response(command, abstract):
    # Configure the API each time to ensure it's loaded
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        return "API key not configured. Please set the gemini_key environment variable."
    # Create a GenerationConfig and set safety settings
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(instruction_dict[command] + abstract)
        return response.text
    except Exception as e1:
        print(f"First model attempt failed: {e1}")
        try:
            # Fall back to gemini-1.5-pro if the first one fails
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(instruction_dict[command] + abstract)
            return response.text
        except Exception as e2:
            print(f"Second model attempt failed: {e2}")
            try:
                # As a last resort, try with a simpler model
                model = genai.GenerativeModel('gemini-1.0-pro')
                response = model.generate_content(instruction_dict[command] + abstract)
                return response.text
            except Exception as e3:
                print(f"All model attempts failed: {e3}")
                return "AI response generation failed. Please check your API key and available models."