# ======================================================================
# FILE:        test_api.py
# PLACE IN:    C:\CompilerDesignProjects\regex-dfa-backend\test_api.py
#              (replace the existing file; do NOT copy into Regex_DFA_Visualizer_backup)
# PURPOSE:     API tests for main.py.
# RUN / CHECK (PowerShell):
#   cd C:\CompilerDesignProjects\regex-dfa-backend
#   ..\.venv\Scripts\python.exe -m unittest -v test_api.py
# ======================================================================
"""API-level regression tests. Run from this folder with: python -m unittest -v test_api.py"""
import unittest

from fastapi import HTTPException

from main import AutomataRequest, create_automata, make_complete_dfa, describe_symbols
from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


def run(regex, text="", minimize=False):
    return create_automata(AutomataRequest(regex=regex, test_string=text, minimize=minimize))


class TestRegexLabAPI(unittest.TestCase):
    def test_reported_examples_are_accepted(self):
        for regex, value in (("a*b*(a|b)", "abb"), ("a*bb", "abb")):
            with self.subTest(regex=regex):
                self.assertTrue(run(regex, value)["test"]["accepted"])

    def test_single_space_regex_is_allowed(self):
        self.assertTrue(run(" ", " ")["test"]["accepted"])

    def test_invalid_regex_returns_controlled_422(self):
        with self.assertRaises(HTTPException) as caught:
            run("a**")
        self.assertEqual(caught.exception.status_code, 422)
        self.assertIn("Invalid regular expression", caught.exception.detail)

    def test_completed_dfa_has_every_declared_transition(self):
        complete = make_complete_dfa(convert_nfa_to_dfa(build_simple_nfa("a|b"), minimize=False))
        for state in range(len(complete["states"])):
            for symbol in complete["alphabet"]:
                self.assertIn(symbol, complete["transitions"][state])

    def test_dead_state_is_rejecting_and_loops(self):
        dfa = make_complete_dfa(convert_nfa_to_dfa(build_simple_nfa("a"), minimize=False))
        dead = dfa["dead_state"]
        self.assertIsNotNone(dead)
        self.assertNotIn(dead, dfa["accept_states"])
        for symbol in dfa["alphabet"]:
            self.assertEqual(dfa["transitions"][dead][symbol], dead)

    def test_rejection_goes_through_dead_state(self):
        test = run("ab", "ba")["test"]
        self.assertFalse(test["accepted"])
        self.assertEqual(test["steps"][0]["next_state"], test["path"][1])
        self.assertTrue(all(step["next_state"] for step in test["steps"]))

    def test_unicode_test_string_with_wildcard(self):
        self.assertTrue(run("a.", "aé")["test"]["accepted"])

    def test_symbol_outside_alphabet(self):
        test = run("a+", "aZ")["test"]
        self.assertFalse(test["accepted"])
        self.assertEqual(test["steps"][-1]["reason"], "not in alphabet")

    def test_transition_table_covers_whole_alphabet(self):
        table = run("a.c")["transition_table"]
        self.assertEqual(sum(col["size"] for col in table["columns"]), table["alphabet_size"])
        for row in table["rows"]:
            self.assertTrue(all(row["transitions"][col["key"]] for col in table["columns"]))

    def test_minimize_option_shrinks(self):
        raw = run("(a|b)*abb")["stats"]["dfa_states"]
        small = run("(a|b)*abb", minimize=True)["stats"]["dfa_states"]
        self.assertEqual(small, 4)
        self.assertLessEqual(small, raw)

    def test_labels(self):
        self.assertEqual(describe_symbols({"a", "b", "c"}, "abcd"), "a-c")
        self.assertEqual(describe_symbols(set("abcd"), "abcd"), "Σ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
