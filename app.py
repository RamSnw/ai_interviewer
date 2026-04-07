import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from interviewer.job_loader import load_job_descriptions
from interviewer.llm import generate_first_question, generate_next_question, summarize_interview
from interviewer.validation import validate_answer


# Folder where finished interviews will be saved as JSON files.
OUTPUT_FOLDER = Path("interviews")

# Optional logo file for the app header.
# If the image exists, Streamlit will show it.
LOGO_PATH = Path("assets/yonder_logo.png")

# Total number of interview questions shown to the candidate.
TOTAL_QUESTIONS = 4


def ensure_output_folder_exists() -> None:
    """
    Make sure the interviews folder exists before saving files.

    This prevents errors when we try to write the final JSON output.
    """
    OUTPUT_FOLDER.mkdir(exist_ok=True)


def save_interview(
    job_title: str,
    file_name: str,
    history: list[dict],
    summary: str,
    ended_early: bool
) -> str:
    """
    Save the interview transcript and summary to a JSON file.

    We also store whether the candidate finished all questions
    or ended the interview early.
    """
    ensure_output_folder_exists()

    # Use the current date and time to give each saved file
    # a unique name.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_FOLDER / f"interview_{timestamp}.json"

    # This is the data structure that will be written to disk.
    # It contains the interview metadata, all answers, and the summary.
    data = {
        "timestamp": timestamp,
        "job_role": job_title,
        "job_description_file": file_name,
        "questions_answered": len(history),
        "ended_early": ended_early,
        "transcript": history,
        "summary": summary,
    }

    # Save the file in readable JSON format.
    output_path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )
    return str(output_path)


def initialize_session_state() -> None:
    """
    Set up the values the app needs to remember while the user
    moves through the interview.

    We use session state so the selected job, generated questions,
    answers, and summary are not lost every time Streamlit reruns.
    """
    defaults = {
        "selected_job_title": None,
        "selected_job_file": None,
        "selected_job_text": None,
        "started": False,
        "current_question_number": 1,
        "question_bank": {},
        "answers": {},
        "error_message": "",
        "finished": False,
        "ended_early": False,
        "summary": "",
        "saved_path": "",
    }

    # Only set these values if they are missing.
    # This lets Streamlit keep the current interview state
    # between reruns.
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_interview() -> None:
    """
    Reset the interview state when the user starts over.

    We keep the selected job, but clear everything related to the
    current interview run.
    """
    st.session_state.started = False
    st.session_state.current_question_number = 1
    st.session_state.question_bank = {}
    st.session_state.answers = {}
    st.session_state.error_message = ""
    st.session_state.finished = False
    st.session_state.ended_early = False
    st.session_state.summary = ""
    st.session_state.saved_path = ""


def get_question(question_number: int) -> str:
    """
    Return the exact stored question if it already exists.

    This matters because if the user goes back, the previous
    question must stay the same and must not be regenerated.

    If the question was not generated yet, create it now and store it.
    """
    question_bank = st.session_state.question_bank

    # Reuse the existing question if we already generated it before.
    # This keeps the interview stable when the user moves back and forth.
    if question_number in question_bank:
        return question_bank[question_number]

    job_title = st.session_state.selected_job_title
    job_text = st.session_state.selected_job_text

    # Build the interview history from earlier answered questions.
    # The LLM uses this history to generate follow-up questions
    # that fit the previous answers.
    history = []
    for i in range(1, question_number):
        if i in question_bank and i in st.session_state.answers:
            history.append({
                "question_number": i,
                "question": question_bank[i],
                "answer": st.session_state.answers[i],
            })

    # Question 1 is fixed.
    # Questions 2–4 are generated based on the job description
    # and the previous answers.
    if question_number == 1:
        question = generate_first_question(job_title)
    else:
        question = generate_next_question(
            job_title=job_title,
            job_description_text=job_text,
            history=history,
            next_question_number=question_number,
        )

    # Save the generated question so it can be reused later.
    question_bank[question_number] = question
    return question


def build_history() -> list[dict]:
    """
    Build the full transcript from the stored questions and answers.

    This is used for the final AI summary and for saving the interview.
    """
    history = []

    for question_number in sorted(st.session_state.answers.keys()):
        history.append({
            "question_number": question_number,
            "question": st.session_state.question_bank[question_number],
            "answer": st.session_state.answers[question_number],
        })

    return history


# Configure the Streamlit page before drawing the UI.
st.set_page_config(page_title="Yonder Interviewer", page_icon="💬", layout="centered")

# Make sure the session state exists before using it.
initialize_session_state()

# Show the logo only if the image file exists.
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=180)

# App title and short subtitle.
st.title("Yonder Interviewer")
st.caption("A simple AI-powered interview practice app")

# Load all available job descriptions from the text files.
jobs = load_job_descriptions()

# If there are no job files, stop the app and show an error.
if not jobs:
    st.error("No job descriptions were found in the 'job_descriptions' folder.")
    st.stop()

# Build the dropdown using the job titles from the loaded files.
job_titles = [job["title"] for job in jobs]
selected_title = st.selectbox(
    "Select the job you want to be interviewed for:",
    job_titles
)

# Get the full job entry that matches the selected title.
selected_job = next(job for job in jobs if job["title"] == selected_title)

# Top action buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("Start Interview", use_container_width=True):
        # Store the selected job details in session state so the rest
        # of the interview can use them.
        st.session_state.selected_job_title = selected_job["title"]
        st.session_state.selected_job_file = selected_job["file_name"]
        st.session_state.selected_job_text = selected_job["text"]

        # Reset any previous interview data and start fresh.
        reset_interview()
        st.session_state.started = True
        st.rerun()

with col2:
    if st.button("Reset", use_container_width=True):
        reset_interview()
        st.rerun()

# Main interview flow
if st.session_state.started and not st.session_state.finished:
    qn = st.session_state.current_question_number
    question = get_question(qn)

    st.subheader(f"Question {qn} of {TOTAL_QUESTIONS}")
    st.write(question)

    # If the user already answered this question before,
    # load that answer back into the text area.
    existing_answer = st.session_state.answers.get(qn, "")
    answer = st.text_area(
        "Your answer",
        value=existing_answer,
        key=f"answer_box_{qn}",
        height=140,
        placeholder="Write your answer here..."
    )

    # Show the latest validation error, if there is one.
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    nav1, nav2, nav3 = st.columns(3)

    with nav1:
        if st.button("Back", use_container_width=True):
            # Move to the previous question if possible.
            if qn > 1:
                st.session_state.current_question_number -= 1
                st.session_state.error_message = ""
                st.rerun()

    with nav2:
        if st.button("Next", use_container_width=True):
            # Validate the answer before allowing the user
            # to move to the next question.
            is_valid, message = validate_answer(answer)

            if not is_valid:
                st.session_state.error_message = message
                st.rerun()

            # Save the cleaned answer for the current question.
            st.session_state.answers[qn] = answer.strip()
            st.session_state.error_message = ""

            # If this is not the last question, move forward.
            if qn < TOTAL_QUESTIONS:
                st.session_state.current_question_number += 1
                st.rerun()
            else:
                # If this was the last question, build the final transcript,
                # generate the summary, save the file, and mark the interview
                # as completed.
                history = build_history()
                summary = summarize_interview(
                    st.session_state.selected_job_title,
                    history
                )
                saved_path = save_interview(
                    job_title=st.session_state.selected_job_title,
                    file_name=st.session_state.selected_job_file,
                    history=history,
                    summary=summary,
                    ended_early=False,
                )

                st.session_state.summary = summary
                st.session_state.saved_path = saved_path
                st.session_state.finished = True
                st.session_state.ended_early = False
                st.rerun()

    with nav3:
        if st.button("Finish Early", use_container_width=True):
            # If the user typed something in the current answer box,
            # validate and save it before finishing early.
            if answer.strip():
                is_valid, message = validate_answer(answer)

                if not is_valid:
                    st.session_state.error_message = message
                    st.rerun()

                st.session_state.answers[qn] = answer.strip()

            history = build_history()

            # Only allow early finish if there is at least one answer.
            if history:
                summary = summarize_interview(
                    st.session_state.selected_job_title,
                    history
                )
                saved_path = save_interview(
                    job_title=st.session_state.selected_job_title,
                    file_name=st.session_state.selected_job_file,
                    history=history,
                    summary=summary,
                    ended_early=True,
                )

                st.session_state.summary = summary
                st.session_state.saved_path = saved_path
                st.session_state.finished = True
                st.session_state.ended_early = True
                st.session_state.error_message = ""
                st.rerun()
            else:
                st.session_state.error_message = "Please answer at least one question before finishing."
                st.rerun()

# Final screen shown after the interview ends
if st.session_state.finished:
    # Show a different status message depending on whether
    # the interview was completed or ended early.
    if st.session_state.ended_early:
        st.warning("Interview ended early by candidate.")
    else:
        st.success("Interview completed successfully.")

    st.subheader("Interview Summary")
    st.write(st.session_state.summary)

    st.subheader("Saved File")
    st.code(st.session_state.saved_path)
