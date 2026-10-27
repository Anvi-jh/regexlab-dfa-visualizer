# ======================================================================
# FILE:        test_regex_safety.py
# PLACE IN:    C:\CompilerDesignProjects\Regex_DFA_Visualizer\test_regex_safety.py
#              (replace the existing file; do NOT copy into Regex_DFA_Visualizer_backup)
# PURPOSE:     Regression + correctness tests (compares the DFA with Python's re).
# STEPS:
#   1. Keep test_dfa.py and test_nfa.py as they are; they still pass unchanged.
# RUN / CHECK (PowerShell):
#   cd C:\CompilerDesignProjects\Regex_DFA_Visualizer
#   ..\.venv\Scripts\python.exe -m unittest -v test_dfa.py test_regex_safety.py
#   ..\.venv\Scripts\python.exe test_nfa.py
# ======================================================================
"""Regression tests for parser correctness, DFA rules and resource safeguards."""
import itertools
import re
import unittest

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa, complete_dfa, run_dfa


def accepts(pattern, value, minimize=True):
    nfa = build_simple_nfa(pattern, extra_alphabet=value)
    dfa = complete_dfa(convert_nfa_to_dfa(nfa, minimize=minimize))
    return run_dfa(dfa, value)[0]


class TestRegexSafety(unittest.TestCase):
    def test_reported_examples(self):
        self.assertTrue(accepts("a*b*(a|b)", "abb"))
        self.assertTrue(accepts("a*bb", "abb"))

    def test_negated_shorthand_classes(self):
        self.assertTrue(accepts(r"\D+", "abc"))
        self.assertFalse(accepts(r"\D+", "a5"))
        self.assertTrue(accepts(r"\W+", "!!!"))
        self.assertFalse(accepts(r"\W+", "a!"))
        self.assertTrue(accepts(r"\S+", "abc"))
        self.assertFalse(accepts(r"\S+", "a b"))

    def test_negated_shorthand_inside_class(self):
        self.assertTrue(accepts(r"[\D]+", "abc"))
        self.assertFalse(accepts(r"[\D]+", "a5"))
        self.assertTrue(accepts(r"[\Da]+", "xa"))
        self.assertTrue(accepts(r"[^\d]+", "abc"))
        self.assertFalse(accepts(r"[^\d]+", "a1"))

    def test_hex_escape(self):
        self.assertTrue(accepts(r"\x41+", "AAA"))
        self.assertFalse(accepts(r"\x41+", "AAB"))

    def test_unicode_literal(self):
        self.assertTrue(accepts("é", "é"))
        self.assertFalse(accepts("é", "e"))

    def test_unicode_in_wildcard_and_negation(self):
        # Old bug: '.' and [^...] were resolved before later literals were seen.
        self.assertTrue(accepts(".é", "éé"))
        self.assertTrue(accepts("[^a]", "é"))
        self.assertTrue(accepts(r"é.", "éü"))
        self.assertFalse(accepts("[^é]", "é"))

    def test_wildcard_matches_carriage_return_not_newline(self):
        self.assertTrue(accepts("a.b", "a\rb"))
        self.assertFalse(accepts("a.b", "a\nb"))

    def test_single_space_is_a_valid_pattern(self):
        self.assertTrue(accepts(" ", " "))
        self.assertFalse(accepts(" ", ""))

    def test_open_and_lower_bounded_repetition(self):
        self.assertFalse(accepts("a{2,}", "a"))
        self.assertTrue(accepts("a{2,}", "aaaaa"))
        self.assertTrue(accepts("a{,2}", ""))
        self.assertFalse(accepts("a{,2}", "aaa"))
        self.assertTrue(accepts("a{0}b", "b"))

    def test_brace_literals(self):
        self.assertTrue(accepts("a{", "a{"))
        self.assertTrue(accepts("a{x}", "a{x}"))
        self.assertTrue(accepts("}", "}"))

    def test_unsupported_constructs_are_rejected(self):
        for pattern in (r"\1", r"\bword", r"^a", r"a$", "a**", "a+?", r"\q", "*a", "{2}"):
            with self.subTest(pattern=pattern):
                with self.assertRaises(ValueError):
                    build_simple_nfa(pattern)

    def test_nested_repetition_hits_nfa_limit(self):
        with self.assertRaisesRegex(ValueError, "safety limit"):
            build_simple_nfa("(a{100}){100}")

    def test_dfa_state_limit_is_enforced(self):
        nfa = build_simple_nfa("a|b")
        with self.assertRaisesRegex(ValueError, "safety limit"):
            convert_nfa_to_dfa(nfa, minimize=False, max_states=1)

    def test_unclosed_character_class_is_rejected(self):
        with self.assertRaises(ValueError):
            build_simple_nfa("[abc")

    def test_symbol_outside_alphabet_is_rejected_not_crashed(self):
        dfa = complete_dfa(convert_nfa_to_dfa(build_simple_nfa("a+")))
        accepted, _, steps = run_dfa(dfa, "aé")
        self.assertFalse(accepted)
        self.assertEqual(steps[-1]["reason"], "not in alphabet")


class TestDFAStructure(unittest.TestCase):
    def test_start_is_zero_and_bfs_numbered(self):
        dfa = convert_nfa_to_dfa(build_simple_nfa("abc"), minimize=True)
        self.assertEqual(dfa["start_state"], 0)
        self.assertEqual(dfa["transitions"][0]["a"], 1)
        self.assertEqual(dfa["transitions"][1]["b"], 2)

    def test_minimal_state_counts(self):
        # Known minimal partial DFA sizes (no dead state).
        cases = {"a*": 1, "(a|b)*": 1, "a(b|c)*": 2, "a*b*(a|b)": 4,
                 "(a|b)*abb": 4, "abc": 4, "a{2,4}": 5}
        for pattern, expected in cases.items():
            with self.subTest(pattern=pattern):
                dfa = convert_nfa_to_dfa(build_simple_nfa(pattern), minimize=True)
                self.assertEqual(len(dfa["states"]), expected)

    def test_complete_dfa_dead_state_rules(self):
        dfa = complete_dfa(convert_nfa_to_dfa(build_simple_nfa("ab"), minimize=False))
        dead = dfa["dead_state"]
        self.assertIsNotNone(dead)
        self.assertNotIn(dead, dfa["accept_states"])
        for state in range(len(dfa["states"])):
            for symbol in dfa["alphabet"]:
                self.assertIn(symbol, dfa["transitions"][state])
        for symbol in dfa["alphabet"]:
            self.assertEqual(dfa["transitions"][dead][symbol], dead)

    def test_no_dead_state_when_already_complete(self):
        dfa = complete_dfa(convert_nfa_to_dfa(build_simple_nfa("(a|b)*")))
        self.assertIsNone(dfa["dead_state"])

    def test_minimized_is_never_larger(self):
        for pattern in ("(a|b)*abb", "a*b*(a|b)", "(ab|cd)*", "[a-c]{1,3}x"):
            nfa = build_simple_nfa(pattern)
            raw = convert_nfa_to_dfa(nfa, minimize=False)
            small = convert_nfa_to_dfa(nfa, minimize=True)
            self.assertLessEqual(len(small["states"]), len(raw["states"]))


class TestAgainstPythonRe(unittest.TestCase):
    """Brute-force check: the DFA must agree with re.fullmatch (ASCII mode)
    on every string over a small alphabet up to length 5."""

    PATTERNS = [
        "a", "ab", "a|b", "a*", "a+", "a?", "(ab)*", "(a|b)*abb", "a*b*(a|b)",
        "a*bb", "(ab|ba)+", "a{2,4}", "a{2,}", "(a|b){,2}c?", "[ab]c*",
        "[^a]b", r"\d+", r"\D", r"\w\W", r"\s?a", ".a", "a.b", "(a|)b",
        "((a|b)c)*", "a(b|c)*", "(a*|b*)*", "[a-c]+x?", r"a\.b", "a|b|c|",
    ]
    ALPHABET = "abcx1 ."

    def test_equivalence(self):
        strings = [""]
        for length in range(1, 6):
            strings.extend("".join(t) for t in itertools.product(self.ALPHABET, repeat=length))
        for pattern in self.PATTERNS:
            compiled = re.compile(pattern, re.ASCII)
            nfa = build_simple_nfa(pattern)
            for minimize in (False, True):
                dfa = complete_dfa(convert_nfa_to_dfa(nfa, minimize=minimize))
                for text in strings:
                    expected = compiled.fullmatch(text) is not None
                    actual = run_dfa(dfa, text)[0]
                    if expected != actual:
                        self.fail(f"{pattern!r} on {text!r}: re={expected}, dfa={actual}, minimize={minimize}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
