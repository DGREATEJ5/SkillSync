import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def enhance_job_matches(resume_text: str, matches: list) -> str:
    """
    Take the resume text and top job matches from RAG,
    then ask GPT to summarize and give job recommendations.
    Returns a string with human-friendly recommendations.
    """

    matches_text = "\n".join([
        f"{i+1}. {m['title']} - {m['description']} (Skills: {', '.join(m['skills'])})"
        for i, m in enumerate(matches)
    ])

    prompt = f"""
You are a helpful career assistant AI.

Here is a candidate's resume:
\"\"\"{resume_text}\"\"\"

Top job matches:
{matches_text}

Provide a clear, concise recommendation for the candidate, highlighting why these jobs fit their skills and experience.
Also remove "**" or other like that. Remove asterisk from the text. or bullets.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful career assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()
