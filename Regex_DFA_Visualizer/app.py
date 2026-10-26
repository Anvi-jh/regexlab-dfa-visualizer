
import streamlit as st

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa
from automata_visualizer import (
    create_nfa_diagram,
    create_dfa_diagram,
)

st.set_page_config(
    page_title="Regex to DFA Visualizer",
    layout="wide",
)

st.title("Regex to DFA Visualizer")
st.write(
    "Convert a regular expression into an NFA and DFA, "
    "then test whether a string is accepted."
)

with st.expander("Regex Syntax Guide"):
    st.markdown(
        r"""
        | Symbol | Meaning | Example |
        |---|---|---|
        | `AB` | Concatenation | `ab` |
        | `A\|B` | Either expression | `cat\|dog` |
        | `( )` | Grouping | `(ab\|cd)` |
        | `*` | Zero or more repetitions | `a*` |
        | `+` | One or more repetitions | `a+` |
        | `?` | Zero or one occurrence | `colou?r` |
        | `[abc]` | Any listed character | `[abc]+` |
        | `[a-z]` | Character range | `[a-z]+` |
        | `[^0-9]` | Any character except digits | `[^0-9]+` |
        | `.` | Any supported character except newline | `a.c` |
        | `{m}` | Exactly m repetitions | `a{3}` |
        | `{m,n}` | Between m and n repetitions | `a{2,4}` |
        | `\d` | Digit | `\d+` |
        | `\w` | Word character | `\w+` |
        | `\s` | Whitespace character | `\s+` |
        | `\*` | Literal asterisk | `a\*b` |

        This visualizer supports the regex features implemented in its parser,
        not every feature of advanced regex engines.
        """
    )

regex = st.text_input(
    "Enter Regular Expression",
    value="a(b|c)*",
    max_chars=200,
    key="regex_input",
)

test_string = st.text_input(
    "Enter String to Test",
    value="abcb",
    max_chars=1000,
    key="test_string_input",
)

if st.button("Build Automata and Test", type="primary"):
    if not regex.strip():
        st.warning(
            "Please enter a regular expression before building the automata."
        )

    elif len(regex) > 200:
        st.error("The regular expression is too long. Use at most 200 characters.")

    else:
        try:
            with st.spinner("Building NFA and DFA..."):
                nfa = build_simple_nfa(regex)
                dfa = convert_nfa_to_dfa(nfa)

            st.success("NFA and DFA created successfully.")

            st.subheader("1. NFA Diagram")
            st.graphviz_chart(create_nfa_diagram(nfa))

            st.subheader("2. DFA Diagram")
            st.graphviz_chart(create_dfa_diagram(dfa))

            st.subheader("3. DFA Transition Table")

            table = []

            for state, transitions in dfa["transitions"].items():
                row = {"State": f"D{state}"}

                for symbol in sorted(dfa["alphabet"]):
                    destination = transitions.get(symbol)

                    row[repr(symbol)] = (
                        f"D{destination}"
                        if destination is not None
                        else "-"
                    )

                table.append(row)

            st.dataframe(table, width="stretch")

            st.subheader("4. String Testing")

            current_state = dfa["start_state"]
            path = [f"D{current_state}"]
            steps = []

            for position, character in enumerate(test_string, start=1):
                next_state = (
                    dfa["transitions"]
                    .get(current_state, {})
                    .get(character)
                )

                steps.append(
                    {
                        "Character Position": position,
                        "Character": repr(character),
                        "Current State": f"D{current_state}",
                        "Next State": (
                            f"D{next_state}"
                            if next_state is not None
                            else "No transition"
                        ),
                    }
                )

                if next_state is None:
                    current_state = None
                    break

                current_state = next_state
                path.append(f"D{current_state}")

            accepted = (
                current_state is not None
                and current_state in dfa["accept_states"]
            )

            if accepted:
                st.success("String ACCEPTED by the regular expression.")
            else:
                st.error("String REJECTED by the regular expression.")

            st.write("Execution path:", " → ".join(path))

            st.write("Step-by-step transitions:")
            if steps:
                st.dataframe(steps, width="stretch")
            else:
                st.info(
                    "The input string is empty. "
                    "Acceptance depends on whether the regex matches an empty string."
                )

        except (ValueError, SyntaxError) as error:
            st.error(f"Invalid regular expression: {error}")

        except Exception as error:
            st.error(
                "The automata could not be generated. "
                "Please check your inputs and try again."
            )
            st.caption(f"Technical details: {error}")
