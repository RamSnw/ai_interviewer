# ai_interviewer
A simple AI-powered interview practice app built with Streamlit and Ollama.
# Yonder Interviewer

Yonder Interviewer is a simple AI-powered interview practice app built with **Python**, **Streamlit**, and **Ollama**.

The app allows a candidate to select a job role from a list of available job descriptions, answer interview questions one by one, and receive an AI-generated summary at the end.

The project was designed to stay simple, practical, and easy to understand.

---

## Features

- Streamlit web interface
- Dropdown for selecting a job role
- Uses local job description text files as input
- Generates **4 interview questions**
- Questions are shown **one by one**
- The first question asks whether the candidate already has experience in the selected role or is transitioning into it
- Later questions take previous answers into account
- The candidate can go back to the previous question
- Previous questions stay exactly the same and are not regenerated
- Basic input validation for:
  - blank answers
  - spaces only
  - gibberish
  - inappropriate language
- Final AI-generated interview summary
- Saves completed interviews as JSON files in the `interviews/` folder
- Yonder logo support

---

## Project Structure

```text
ai_interviewer/
├── app.py
├── requirements.txt
├── interviews/
├── assets/
│   └── yonder_logo.png
├── job_descriptions/
│   ├── AI Engineer.txt
│   ├── Backend Developer.txt
│   ├── Business Analyst.txt
│   ├── Data Analyst.txt
│   ├── Data Engineer.txt
│   ├── DevOps Engineer.txt
│   ├── Frontend Developer.txt
│   ├── Product Manager.txt
│   ├── QA Engineer.txt
│   ├── Recruiter HR Specialist.txt
│   └── UI UX Designer.txt
└── interviewer/
    ├── __init__.py
    ├── job_loader.py
    ├── llm.py
    └── validation.py
