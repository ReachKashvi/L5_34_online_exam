# Lab 5 — Reflection

> The handout's four reflection questions are reproduced below in the form they were given in the lab brief. If the wording in your copy of the handout differs, the answers still cover the same ground.

## 1. Which tool did you find most useful, and why?

**Bandit**, because it was the only one of the three that found problems that could actually hurt someone. Pylint and Flake8 told me the code was untidy; Bandit told me that `os.system("ssh " + labPc + " lock-screen")` would hand a shell to anyone who could choose the hostname, and that marks were being decided by an MD5 comparison. Those two were rated High severity and neither is visible by just running the program — the demo never calls `lock_screen()` at all, so no amount of testing would have surfaced it.

That said, **Pylint** found the bug I would have been most likely to ship: the mutable default argument `penalties={}`. The program printed correct-looking output, so nothing felt wrong, but the dictionary is created once at definition time and shared by every call. I confirmed it — after grading two students, the default held `{'Anil': 3, 'Divya': 3}`, meaning one student's penalty data leaks into the next student's exam session. Pylint flagged it in a second as `W0102`.

Flake8 was the least interesting but the fastest to act on: four violations, all fixed in under a minute.

## 2. What types of issues were most common in your code?

By count, **style and convention issues dominated**. Of Pylint's 20 messages, 9 were missing docstrings and 8 were camelCase names that should have been `snake_case` — 17 of 20 messages were naming and documentation, not logic. Flake8 added four more purely cosmetic ones (missing blank line, no spaces around `=`, inline comment spacing, a 93-character line).

The genuinely dangerous issues were far fewer but far more serious: two High-severity security findings (command injection, weak MD5), two Low-severity ones (hardcoded password, predictable `random`), and three real quality defects (mutable default argument, `range(len(...))` indexing, an `elif` chain after `return`).

The pattern I take from that: **the noisy issues and the dangerous issues are not the same issues.** Counting findings tells you nothing useful; you have to sort by severity. That is why I fixed the Bandit High findings first and left the blank lines for last.

## 3. How did static analysis help improve the quality and security of your code?

In four distinct ways:

- **It found bugs in code that was never executed.** `lock_screen()` is dead code in the demo, so running the program could never have revealed the injection flaw. Static analysis reads every line whether or not it runs.
- **It found bugs that produce correct output.** The `penalties={}` default never caused a visible wrong answer in this demo, but it is a genuine data-leak between exam sessions. Testing would only have caught it with a test written specifically to check the default — which I would not have thought to write.
- **It named the risk precisely.** Bandit gave me CWE-78 for the injection and CWE-327 for MD5, with links. That turned "this looks sketchy" into something I could look up, understand and explain.
- **It made the code readable.** The docstrings and snake_case renames do not change behaviour at all, but the next person to open this file — including me in a month — can now tell what `hash_answer` does without tracing its calls.

Concretely: Pylint went from **5.65/10 to 10.00/10**, Bandit from **2 High + 2 Low to 0**, Flake8 from **4 violations to 0**, and the program still prints exactly the same scores, grades, average and topper.

## 4. What are the limitations of static analysis, and would you use it in your own workflow?

**Limitations I ran into directly:**

- **It cannot tell intent from risk.** Bandit flagged `random.choice()` for picking a bonus question as a security issue. In a different program that would be a false positive worth ignoring; in an exam program a predictable question order genuinely matters, so I fixed it. The tool could not make that judgement — I had to.
- **Fixing one finding can raise others.** Replacing `os.system` with `subprocess.run` cleared the High-severity B605 but raised three new Low ones (B404, B603, B607) simply for using `subprocess` at all. I fixed B607 properly with `shutil.which()`, and marked B404 and B603 with `# nosec` plus a reason. Taking the report as a score to drive to zero, rather than a list to think about, would have pushed me the wrong way here.
- **It misses whole categories of bug.** Neither tool noticed that `main()` was called at import time, or that `topper()` raises `ValueError` on an empty class. I found both by reading the code. Static analysis checks patterns it knows; it does not know what the program is supposed to do.
- **Style findings can drown the real ones.** 17 of 20 Pylint messages were cosmetic. On a larger file the two High-severity security issues would have been easy to scroll past.

**Would I use it?** Yes — but configured, not raw. I would run Flake8 and Pylint on save in the editor so style never accumulates in the first place, and run Bandit in CI as a gate on High and Medium severity only, so a pull request cannot merge with a command injection in it. Low-severity informational findings I would review, not block on. The one habit I am taking from this lab: **run the tools before asking someone to review the code**, so the reviewer spends their time on the logic instead of pointing out my blank lines.
