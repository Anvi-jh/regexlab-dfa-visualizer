# RegexLab — Regex-to-DFA Visualizer

RegexLab demonstrates Thompson NFA construction and subset construction to a DFA. The Streamlit app uses the core Python modules directly; the React app calls the FastAPI backend.

## Supported syntax

- Concatenation: `ab`
- Alternation: `a|b`
- Grouping: `(ab)`
- Repetition: `a*`, `a+`, `a?`, `{m}`, `{m,n}`
- Character classes and ranges: `[abc]`, `[a-z]`, `[^0-9]`
- Shorthand classes: `\d`, `\D`, `\w`, `\W`, `\s`, `\S`
- Escaped punctuation and control/hex escapes: `\*`, `\n`, `\t`, `\x41`, `\u00E9`
- Wildcard: `.` (except CR/LF)

The parser deliberately rejects unsupported syntax rather than guessing. Unsupported constructs include anchors `^`/`$`, word boundaries `\b`/`\B`, backreferences, open-ended bounded repetitions such as `{2,}`, lazy/possessive quantifiers, and unknown alphabetic escapes. To match a punctuation character literally, escape it where needed.

## Alphabet semantics and Unicode note

To keep the DFA finite and suitable for visualization, the alphabet is ASCII plus non-ASCII literal characters explicitly present in the pattern. Unicode literals such as `é` work. The implementation does **not** claim full Python `re` Unicode semantics for wildcard or negated classes: characters outside the declared finite alphabet are not represented by the DFA. This is an explicit limitation, not silent full-Unicode compatibility.

## Safety limits

- Regex length: 200 characters
- Syntax tree nodes: 1,500
- NFA states: 5,000
- DFA states: 1,000 in the conversion used by the API
- Bounded repetition maximum: 100
- Character range size: 10,001 code points

Exceeding a limit returns a controlled error instead of allowing unbounded state growth.

## Run the Streamlit version

From `C:\CompilerDesignProjects`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\Regex_DFA_Visualizer\app.py
```

## Run the React + FastAPI version

Backend terminal:

```powershell
cd C:\CompilerDesignProjects
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --app-dir .\regex-dfa-backend --port 8000
```

Frontend terminal:

```powershell
cd C:\CompilerDesignProjects\regex-dfa-frontend
npm run dev
```

- Frontend: `http://localhost:5173`
- API docs: `http://127.0.0.1:8000/docs`

## Run tests

Core tests (PowerShell terminal):

```powershell
cd C:\CompilerDesignProjects\Regex_DFA_Visualizer
..\.venv\Scripts\python.exe -m unittest -v test_dfa.py test_regex_safety.py
..\.venv\Scripts\python.exe test_nfa.py
```

Backend/API tests:

```powershell
cd C:\CompilerDesignProjects\regex-dfa-backend
..\.venv\Scripts\python.exe -m unittest -v test_api.py
```

Frontend checks:

```powershell
cd C:\CompilerDesignProjects\regex-dfa-frontend
npm run build
npm run lint
```
