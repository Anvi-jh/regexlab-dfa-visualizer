"""Regression tests for parser correctness and resource safeguards."""
import unittest

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


def accepts(pattern, value):
    dfa = convert_nfa_to_dfa(build_simple_nfa(pattern))
    state = dfa["start_state"]
    for character in value:
        state = dfa["transitions"].get(state, {}).get(character)
        if state is None:
            return False
    return state in dfa["accept_states"]


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

    def test_hex_escape(self):
        self.assertTrue(accepts(r"\x41+", "AAA"))
        self.assertFalse(accepts(r"\x41+", "AAB"))

    def test_unicode_literal(self):
        self.assertTrue(accepts("é", "é"))
        self.assertFalse(accepts("é", "e"))

    def test_single_space_is_a_valid_pattern(self):
        self.assertTrue(accepts(" ", " "))
        self.assertFalse(accepts(" ", ""))

    def test_unsupported_constructs_are_rejected(self):
        for pattern in (r"\1", r"\bword", r"^a", r"a$", "a**", "a+?", r"\q"):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
