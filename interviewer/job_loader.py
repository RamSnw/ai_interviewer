from pathlib import Path


# This points to the folder where all job description text files are stored.
# We use Path because it makes file and folder handling cleaner in Python.
JOB_FOLDER = Path("job_descriptions")


def read_text_file(file_path: Path) -> str:
    """
    Read one job description file and return its text.

    We use UTF-8 encoding because it is the safest default for text files.
    strip() removes extra empty spaces or blank lines at the start and end.
    """
    return file_path.read_text(encoding="utf-8").strip()


def extract_job_title(file_name: str, text: str) -> str:
    """
    Try to read the job title from the file content.

    The files are expected to contain a line like:
    JOB TITLE: AI Engineer

    If that line exists, we use it because it is the clearest source.
    If that line is missing, we fall back to the file name without '.txt'.
    """
    for line in text.splitlines():
        # Remove extra spaces around each line before checking it.
        clean_line = line.strip()

        # We compare in uppercase so the check still works even if
        # the text file uses 'Job Title:' or 'job title:'.
        if clean_line.upper().startswith("JOB TITLE:"):
            # split(":", 1) breaks the line into two parts:
            # - left side: JOB TITLE
            # - right side: the actual title
            # [1] means we keep the right side only.
            return clean_line.split(":", 1)[1].strip()

    # Fallback: if the file does not contain a JOB TITLE line,
    # use the file name itself as the title.
    return file_name.replace(".txt", "").strip()


def load_job_descriptions() -> list[dict]:
    """
    Load all .txt job description files from the job_descriptions folder.

    Each job is returned as a dictionary with:
    - file_name: the original file name
    - title: the extracted job title
    - text: the full file content

    This makes it easy for the rest of the app to:
    - show job names in the dropdown
    - access the full job description when generating questions
    """
    jobs = []

    # If the folder does not exist, return an empty list instead of failing.
    # This keeps the app safer and easier to debug.
    if not JOB_FOLDER.exists():
        return jobs

    # Find all .txt files in the folder.
    # sorted(...) keeps the order consistent every time the app runs.
    for file_path in sorted(JOB_FOLDER.glob("*.txt")):
        text = read_text_file(file_path)

        # Skip empty files so they do not break the app
        # or appear as empty job roles in the dropdown.
        if not text:
            continue

        # Store the file information in a simple dictionary.
        # This structure is enough for the app and keeps the code easy to read.
        jobs.append({
            "file_name": file_path.name,
            "title": extract_job_title(file_path.name, text),
            "text": text,
        })

    return jobs
