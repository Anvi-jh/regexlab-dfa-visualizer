"""API-level regression tests. Run from this folder with: python -m unittest -v test_api.py"""
import unittest

from fastapi import HTTPException

from main import AutomataRequest, create_automata, make_complete_dfa
from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


class TestRegexLabAPI(unittest.TestCase):
    def test_reported_examples_are_accepted(self):
        for regex, value in (("a*b*(a|b)", "abb"), ("a*bb", "abb")):
            with self.subTest(regex=regex):
                result = create_automata(AutomataRequest(regex=regex, test_string=value))
                self.assertTrue(result["test"]["accepted"])

    def test_single_space_regex_is_allowed(self):
        result = create_automata(AutomataRequest(regex=" ", test_string=" "))
        self.assertTrue(result["test"]["accepted"])

    def test_invalid_regex_returns_controlled_422(self):
        with self.assertRaises(HTTPException) as caught:
            create_automata(AutomataRequest(regex="a**"))
        self.assertEqual(caught.exception.status_code, 422)
        self.assertIn("Invalid regular expression", caught.exception.detail)

    def test_completed_dfa_has_every_declared_transition(self):
        partial = convert_nfa_to_dfa(build_simple_nfa("a|b"), minimize=False)
        complete = make_complete_dfa(partial)
        alphabet = complete["alphabet"]
        for state in range(len(complete["states"])):
            for symbol in alphabet:
                self.assertIn(symbol, complete["transitions"][state])

    def test_dead_state_is_rejecting_and_loops(self):
        dfa = make_complete_dfa(convert_nfa_to_dfa(build_simple_nfa("a"), minimize=False))
        dead = dfa.get("dead_state")
        self.assertIsNotNone(dead)
        self.assertNotIn(dead, dfa["accept_states"])
        for symbol in dfa["alphabet"]:
            self.assertEqual(dfa["transitions"][dead][symbol], dead)


if __name__ == "__main__":
    unittest.main(verbosity=2)
