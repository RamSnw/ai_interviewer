import ollama


# This is the Ollama model the app will use for generating
# interview questions and the final summary.
MODEL_NAME = "llama3:latest"


def ask_ollama(prompt: str) -> str:
    """
    Send a prompt to Ollama and return the generated text.

    This is the main helper function used whenever the app needs
    the AI model to generate something.
    """
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # We return only the generated text content.
    # strip() removes extra blank spaces or line breaks.
    return response["message"]["content"].strip()


def clean_single_question(raw_text: str) -> str:
    """
    Keep only the first useful line from the model output.

    Sometimes the model adds numbering or labels like:
    - "1. ..."
    - "Question: ..."
    - "Here is the question: ..."

    This function cleans that up so the app shows one simple question.
    """
    if not raw_text:
        return ""

    # Split the output into lines and keep only non-empty ones.
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return ""

    first_line = lines[0]

    # These are common prefixes the model may add.
    prefixes = [
        "1. ",
        "- ",
        "* ",
        "Question: ",
        "Interviewer: ",
        "Here is the question: "
    ]

    # If the line starts with one of these prefixes,
    # remove it so the final question looks cleaner.
    for prefix in prefixes:
        if first_line.startswith(prefix):
            first_line = first_line[len(prefix):].strip()

    return first_line


def format_history(history: list[dict]) -> str:
    """
    Turn previous questions and answers into text that the model can use.

    The model needs the interview history in plain text so it can
    generate follow-up questions that make sense in context.
    """
    if not history:
        return "No previous questions and answers yet."

    parts = []

    for item in history:
        parts.append(f"Question {item['question_number']}: {item['question']}")
        parts.append(f"Answer {item['question_number']}: {item['answer']}")
        parts.append("")

    return "\n".join(parts)


def generate_first_question(job_title: str) -> str:
    """
    The first question is fixed on purpose.

    We do not ask the model to generate the first question because
    we want it to always be stable, clear, and neutral.

    This avoids the model making strange assumptions about whether
    the candidate already has experience in the role.
    """
    article = "an" if job_title[:1].lower() in "aeiou" else "a"

    return (
        f"Do you already have work experience as {article} {job_title}, "
        f"or are you moving into this kind of role now? "
        f"Please tell me about your background and the skills that make you a good fit."
    )


def generate_next_question(
    job_title: str,
    job_description_text: str,
    history: list[dict],
    next_question_number: int,
) -> str:
    """
    Generate questions 2, 3, and 4 using:
    - the selected role
    - the job description
    - previous answers

    The prompt is kept simple to reduce delays.
    """
    # Convert earlier questions and answers into plain text
    # so the model can understand what was already discussed.
    history_text = format_history(history)

    # Each question number has a rough focus area.
    # This helps keep the interview balanced.
    category_map = {
        2: "role skills and tools",
        3: "problem solving",
        4: "motivation and teamwork",
    }

    category = category_map.get(next_question_number, "general follow-up")

    # Build the prompt that will be sent to Ollama.
    # We include the selected role, the job description,
    # the interview history, and some rules for the model.
    prompt = f"""
You are an HR interviewer.

Target role:
{job_title}

Job description:
{job_description_text}

Interview history:
{history_text}

Now write question number {next_question_number}.

Focus area:
{category}

Rules:
- Ask only one question
- Use simple, direct language
- Make the question easy to understand
- Use the job description naturally
- Use the previous answers naturally
- Do not ask theory or definition questions
- Do not repeat earlier questions
- Keep it to one sentence if possible
- Do not include numbering
- Do not include explanations
"""

    # Ask Ollama to generate the next question,
    # then clean the result before using it in the app.
    result = clean_single_question(ask_ollama(prompt))

    if result:
        return result

    # Fallback questions are used only if the model fails
    # to return something usable.
    fallback_map = {
        2: f"What tools, tasks, or skills from the {job_title} role have you used the most so far?",
        3: f"Can you tell me about a difficult problem you solved in work or in a project related to this role?",
        4: f"Why do you want this {job_title} role, and how do you usually work with other people to get results?",
    }

    return fallback_map[next_question_number]


def summarize_interview(job_title: str, history: list[dict]) -> str:
    """
    Generate the final summary and light analysis.

    At the end of the interview, we send the full transcript
    to the model and ask it to produce a short structured summary.
    """
    history_text = format_history(history)

    prompt = f"""
You are summarizing a job interview for the role "{job_title}".

Interview transcript:
{history_text}

Write a short, clear summary with exactly these sections:

Summary:
- 3 to 5 sentences about the candidate's answers.

Main Themes:
- 3 to 5 bullet points with the key ideas mentioned.

Sentiment:
- 2 to 3 sentences about the overall tone, confidence, and communication style.

Keep the writing simple, professional, and easy to read.
"""

    return ask_ollama(prompt)
