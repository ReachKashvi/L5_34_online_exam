# Lab 5 — Static Code Analysis: Issues Found and Fixed

**File analysed:** `online_exam.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 (Python 3.12.10, in a virtual environment)

## Summary of results

| Tool | Before | After |
|------|--------|-------|
| Pylint | **5.65/10** — 20 messages | **10.00/10** — 0 messages |
| Bandit | **2 High + 2 Low** severity issues | **0 issues** (2 low/informational reviewed and annotated) |
| Flake8 | **4** style violations | **0** violations |

The program's behaviour is unchanged — it prints the same bonus question, scores, grades, class average and topper as before.

## Issue table

High and medium severity first, then quality, then style.

| # | Issue | Type (Tool / Code) | Line(s) (original) | Description | Fix Approach |
|---|-------|--------------------|--------------------|-------------|--------------|
| 1 | Command injection via `os.system` | **Security — Bandit B605, High severity, CWE-78** | 56 | `os.system("ssh " + labPc + " lock-screen")` builds a shell command by string concatenation. A hostname such as `pc1; rm -rf /` would be parsed by the shell and run as a second command on the lab machine. | Replaced with `subprocess.run([ssh, lab_pc, "lock-screen"], check=True)` — an argument list with `shell=False`, so no shell parsing happens. Added a hostname regex check that raises `ValueError` on anything that is not a plain hostname, and resolved the `ssh` binary with `shutil.which()` so no partial path is executed (this clears Bandit B607 as well). |
| 2 | Weak MD5 hash used to compare answers | **Security — Bandit B324, High severity, CWE-327** | 16 | `hashlib.md5()` is a broken hash function; collisions are cheap to produce, so two different answers can be made to hash alike. Flagged High because the hash decides whether a student gets the mark. | Switched to `hashlib.sha256()`, which is collision-resistant. The signature and behaviour of the function are identical, so grading is unaffected. (Passing `usedforsecurity=False` would silence the warning, but changing the algorithm is the real fix.) |
| 3 | Hardcoded password in source | **Security — Bandit B105, Low severity / Medium confidence, CWE-259** | 11 | `PROCTOR_PASSWORD = "proctor-demo"` puts a credential in the source file, so it travels into Git history and is visible to anyone with read access to the repository. | Read it from the environment instead: `PROCTOR_PASSWORD = os.environ.get("PROCTOR_PASSWORD", "")`. No secret value remains in the file. |
| 4 | Insecure random generator | **Security — Bandit B311, Low severity, CWE-330** | 20 | `random.choice()` uses the Mersenne Twister, which is predictable — an observer who sees enough draws can work out which bonus question comes next, which matters in an exam setting. | Switched to `secrets.choice()`, which draws from the operating system's cryptographic source. Removed the now-unused `random` import. |
| 5 | Mutable default argument | **Quality — Pylint W0102 (dangerous-default-value)** | 23 | `def gradeStudent(studentName, responses, penalties={})` — the `{}` is created **once**, when the function is defined, and is then shared by every call. Penalty counts accumulate across students and across exam runs instead of starting fresh. | Changed the default to `None` and built a new dictionary inside the function: `if penalties is None: penalties = {}`. **Verified:** in the original code, after grading two students the shared default held `{'Anil': 3, 'Divya': 3}`; in the fixed code the default stays `None` and each call gets its own dictionary. |
| 6 | Looping over `range(len(...))` | **Quality — Pylint C0200 (consider-using-enumerate)** | 25 | `for i in range(len(QUESTIONS))` followed by indexing `QUESTIONS[i]` is an index-juggling pattern that invites off-by-one mistakes and reads poorly. | Rewrote as `for index, question in enumerate(QUESTIONS)` and used `question["answer"]` directly. |
| 7 | Unnecessary `elif` / `else` after `return` | **Quality — Pylint R1705 (no-else-return)** | 37–42 | In `getGrade` every branch returns, so the `elif` / `else` chain adds nesting without adding meaning. | Flattened to successive `if percent >= 90: return "A"`, `if percent >= 60: return "B"`, `return "C"`. |
| 8 | camelCase names throughout | **Quality — Pylint C0103 (invalid-name), 8 occurrences** | 15, 19, 23, 35, 54 | Names such as `hashAnswer`, `pickBonusQuestion`, `gradeStudent`, `studentName`, `getGrade`, `classAverage`, `lockScreen` and `labPc` break PEP 8, which specifies `snake_case` for functions and variables. | Renamed everything to snake_case (`hash_answer`, `pick_bonus_question`, `grade_student`, `student_name`, `get_grade`, `class_average`, `lock_screen`, `lab_pc`) and updated every call site. |
| 9 | Missing docstrings | **Quality — Pylint C0114 / C0116, 9 occurrences** | 1, 15, 19, 23, 35, 45, 51, 54, 59 | Neither the module nor any function documented what it does, so a reader has to reconstruct the intent from the code. | Added a module docstring and a one-line docstring to every function; `grade_student` has a longer one explaining the `penalties` argument. |
| 10 | `main()` called at import time | **Quality — latent bug, not tool-reported** | 73 | The bare `main()` call at the bottom runs the whole demo the moment the module is imported — including from a test file or another script. | Guarded it with `if __name__ == "__main__": main()`. |
| 11 | `topper()` crashes on an empty class | **Quality — latent bug, not tool-reported** | 51–52 | `max(results, key=results.get)` raises `ValueError: max() arg is an empty sequence` when no student has been graded, while `class_average()` already handled that case by returning 0. | Added an early `if not results: return None`, matching the defensive style of `class_average()`. |
| 12 | Missing blank line before function | **Style — Flake8 E302** | 54 | `def lockScreen` had only one blank line above it; PEP 8 requires two between top-level definitions. | Added the second blank line. |
| 13 | Missing whitespace around `=` | **Style — Flake8 E225** | 67 | `average=classAverage()` has no spaces around the assignment operator. | Written as `average = class_average()`. |
| 14 | Inline comment spacing | **Style — Flake8 E261** | 69 | `print("Topper:", topper()) # highest score` — PEP 8 requires at least two spaces before an inline comment. | Put two spaces before the `#`. |
| 15 | Line too long | **Style — Flake8 E501** | 70 | The final `print` was 93 characters, over the 79-character limit. | Split the arguments across two lines with aligned continuation. |

## Note on the two remaining Bandit annotations

After the fixes Bandit reports **no issues**, with two findings explicitly marked `# nosec` in the code:

- **B404** (`import subprocess`) — an informational notice that fires on *any* use of the module.
- **B603** (`subprocess` call without `shell=True`) — fires on every `subprocess` call made with an argument list, asking the developer to confirm the input is trusted.

Both are Low severity and are the expected residue of fixing issue #1 properly: the dangerous `os.system` call (High, CWE-78) was replaced with the safe argument-list form, and the hostname is validated against a regex before it is used. Each `# nosec` carries the test id and a comment giving the reason, so the suppression is auditable rather than blanket.

## Commands used

```
python -m venv venv
venv\Scripts\activate
python -m pip install pylint bandit flake8

python -m pylint online_exam.py > pylint_report.txt
python -m bandit -r online_exam.py > bandit_report.txt
python -m flake8 online_exam.py > flake8_report.txt
```

Reports before the fixes: `pylint_report.txt`, `bandit_report.txt`, `flake8_report.txt`.
Reports after the fixes: `pylint_report_after.txt`, `bandit_report_after.txt`, `flake8_report_after.txt`.
