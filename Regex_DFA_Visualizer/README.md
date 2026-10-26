
# Regex-to-DFA Visualizer

## 1. Project Overview

The Regex-to-DFA Visualizer is a Python-based application that demonstrates how a regular expression can be converted into a Non-deterministic Finite Automaton (NFA) and then into a Deterministic Finite Automaton (DFA).

The application also allows users to test input strings and check whether they are accepted by the given regular expression.

The project uses Python for the automata logic and Streamlit for the web interface. Graphviz is used to generate visual diagrams of the automata.

## 2. Objectives

- Understand regular expressions and finite automata.
- Convert regular expressions into NFAs.
- Convert NFAs into DFAs using subset construction.
- Display NFA and DFA diagrams.
- Generate a DFA transition table.
- Test strings and display acceptance or rejection.
- Show the sequence of DFA states followed during testing.
- Demonstrate important concepts from Compiler Design.

## 3. Technologies Used

- Python: Implements the main logic.
- Streamlit: Provides the web application interface.
- Graphviz: Generates automata diagrams.
- Python unittest: Tests the functionality.

## 4. Project Workflow

1. The user enters a regular expression.
2. The application parses the expression.
3. Thompson's construction is used to build an NFA.
4. Subset construction converts the NFA into a DFA.
5. Graphviz generates the NFA and DFA diagrams.
6. The application displays the DFA transition table.
7. The user enters a string to test.
8. The DFA processes the characters one by one.
9. The application displays whether the string is accepted or rejected.

## 5. Main Files

- app.py: Main Streamlit application.
- nfa_builder.py: Regular-expression parsing and NFA construction.
- dfa_builder.py: NFA-to-DFA conversion.
- automata_visualizer.py: Automata diagram generation.
- test_nfa.py: NFA-related tests.
- test_dfa.py: DFA-related tests.
- test_visualizer.py: Visualization tests.
- check_dfa.py: Diagnostic checks for DFA behaviour.

## 6. Supported Regular Expression Features

The implementation supports the following features:

- Concatenation, such as `ab`
- Alternation, such as `a|b`
- Grouping, such as `(ab|cd)`
- Kleene star, such as `a*`
- One-or-more repetition, such as `a+`
- Optional expressions, such as `ab?`
- Character classes, such as `[abc]`
- Character ranges, such as `[a-z]`
- Negated character classes, such as `[^0-9]`
- Wildcard, such as `a.c`
- Bounded repetition, such as `a{2,4}`
- Supported escaped characters, such as `\d` and `\s`

This is a simplified educational implementation and does not support every feature of commercial regular-expression engines.

## 7. Installation Requirements

Install Python and Graphviz before running the application.

Install the required Python packages in the project's virtual environment:

```powershell
python -m pip install streamlit graphviz
```

The Graphviz executable must also be installed and accessible to the application.

## 8. Running the Application

Open PowerShell in the project root directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\Regex_DFA_Visualizer\app.py
```

Open the local URL printed by Streamlit in your browser.

## 9. Testing

Run the DFA tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\Regex_DFA_Visualizer -p "test_dfa.py" -v
```

Run all discoverable test files:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\Regex_DFA_Visualizer -v
```

The existing test runs have shown that the 13 DFA test cases pass and that the 17 NFA acceptance cases pass. Run the commands again whenever the code changes.

## 10. Example

Regular expression:

```text
a(b|c)*
```

Input string:

```text
abcb
```

Expected result:

```text
ACCEPTED
```

The expression allows an `a` followed by zero or more occurrences of either `b` or `c`.

For example, `a`, `ab`, `ac`, and `abcb` match this expression, while `bc` does not.

## 11. Limitations

- The parser supports a defined subset of regular-expression syntax.
- Advanced features such as lookarounds and backreferences are not implemented.
- The supported character universe is limited by the current implementation.
- Large expressions may produce large automata and diagrams.
- This project is designed for learning and demonstration rather than production-scale regex processing.

## 12. Future Improvements

- Improve the visual design and usability.
- Make large diagrams easier to explore.
- Add more automated tests and edge cases.
- Improve error messages and validation.
- Add downloadable diagrams and transition tables.
- Provide clearer explanations of each conversion step.

## 13. Conclusion

The Regex-to-DFA Visualizer demonstrates the relationship between regular expressions, NFAs, and DFAs. It provides visual diagrams, transition tables, and string testing to help students understand finite automata and their role in Compiler Design.
