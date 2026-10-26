
from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


def test_string(dfa, text):
    current = dfa["start_state"]

    for char in text:
        next_state = dfa["transitions"].get(current, {}).get(char)

        if next_state is None:
            return False

        current = next_state

    return current in dfa["accept_states"]


tests = [
    ("a*b", "aaab", True),
    ("a|b", "b", True),
    ("a|b", "ab", False),
    ("(a|b)*", "abba", True),
    ("a+", "aaa", True),
    ("a+", "", False),
    ("ab?", "a", True),
    ("ab?", "ab", True),
    ("[a-c]+", "abc", True),
    ("[0-9]+", "12345", True),
    ("a.c", "abc", True),
    (r"a\*b", "a*b", True),
    ("a{2,4}", "aaa", True),
    ("a{2,4}", "aaaaa", False),
    ("(ab|cd)*", "abcd", True),
    ("(ab|cd)*", "ac", False),
    ("[^0-9]+", "hello", True),
]

failed = 0

for regex, text, expected in tests:
    try:
        nfa = build_simple_nfa(regex)
        dfa = convert_nfa_to_dfa(nfa)
        actual = test_string(dfa, text)
        passed = actual == expected

        print(
            f"{'PASS' if passed else 'FAIL'} | "
            f"Regex={regex!r}, Input={text!r}, "
            f"Expected={expected}, Actual={actual}"
        )

        if not passed:
            failed += 1

    except Exception as error:
        failed += 1
        print(f"ERROR | Regex={regex!r}: {error}")

print(f"\nResults: {len(tests) - failed}/{len(tests)} tests passed.")
