"""A small online examination marker.

Picks a bonus question, grades each student's answers against an answer
key, converts raw scores into letter grades, and reports the class
average and the topper.
"""

import hashlib
import os
import re
import secrets
import shutil
# Used only for the fixed, validated command in lock_screen (shell=False).
import subprocess  # nosec B404

QUESTIONS = [
    {"q": "What is 2 + 2?", "answer": "4"},
    {"q": "Which keyword defines a function in Python?", "answer": "def"},
    {"q": "What does CPU stand for?", "answer": "Central Processing Unit"},
    {"q": "Which type is immutable: list or tuple?", "answer": "tuple"},
]
PROCTOR_PASSWORD = os.environ.get("PROCTOR_PASSWORD", "")
HOSTNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$")
results = {}


def hash_answer(text):
    """Return a hash of an answer, ignoring case and surrounding spaces."""
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def pick_bonus_question():
    """Return the text of a randomly chosen bonus question."""
    return secrets.choice(QUESTIONS)["q"]


def grade_student(student_name, responses, penalties=None):
    """Grade one student's responses, record the score and return it.

    Every wrong or missing answer adds one entry to `penalties`, which
    defaults to a fresh dictionary for each call.
    """
    if penalties is None:
        penalties = {}
    score = 0
    for index, question in enumerate(QUESTIONS):
        given = responses.get(index, "")
        if hash_answer(given) == hash_answer(question["answer"]):
            score += 1
        else:
            penalties[student_name] = penalties.get(student_name, 0) + 1
    results[student_name] = score
    return score


def get_grade(score):
    """Convert a raw score into a letter grade."""
    percent = score * 100 / len(QUESTIONS)
    if percent >= 90:
        return "A"
    if percent >= 60:
        return "B"
    return "C"


def class_average():
    """Return the mean score of all graded students, or 0 if there are none."""
    if not results:
        return 0
    return round(sum(results.values()) / len(results), 2)


def topper():
    """Return the highest scoring student's name, or None if there are none."""
    if not results:
        return None
    return max(results, key=results.get)


def lock_screen(lab_pc):
    """Lock the screen of a lab PC. Kept for the lab: unused by the demo."""
    if not HOSTNAME_PATTERN.match(lab_pc):
        raise ValueError(f"invalid lab PC hostname: {lab_pc!r}")
    ssh = shutil.which("ssh")
    if ssh is None:
        raise RuntimeError("no ssh client found on this machine")
    # Reviewed: fixed argument list, shell=False, hostname validated above.
    subprocess.run([ssh, lab_pc, "lock-screen"], check=True)  # nosec B603


def main():
    """Run a short demonstration of the exam marker."""
    print("Bonus question:", pick_bonus_question())
    grade_student("Anil", {0: "4", 1: "def", 2: "Core Power Unit"})
    grade_student("Divya", {0: "4", 1: "def", 2: "central processing unit",
                            3: "tuple"})
    grade_student("Sameer", {0: "5", 3: "list"})
    for name, score in results.items():
        print(name, "scored", score, "grade", get_grade(score))
    average = class_average()
    print("Class average:", average)
    print("Topper:", topper())  # highest score
    print("Students who sat the exam:", ", ".join(sorted(results)),
          "| total:", len(results))


if __name__ == "__main__":
    main()
