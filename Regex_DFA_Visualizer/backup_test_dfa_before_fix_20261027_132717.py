
import unittest

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


def test_regex(regex, test_string):
    """Build the automata and test a string using the DFA."""
    nfa = build_simple_nfa(regex)
    dfa = convert_nfa_to_dfa(nfa)

    current_state = dfa["start_state"]

    for character in test_string:
        next_state = (
            dfa["transitions"]
            .get(current_state, {})
            .get(character)
        )

        if next_state is None:
            return False

        current_state = next_state

    return current_state in dfa["accept_states"]


class TestDFABuilder(unittest.TestCase):

    def test_simple_match(self):
        self.assertTrue(test_regex("abc", "abc"))

    def test_simple_rejection(self):
        self.assertFalse(test_regex("abc", "abd"))

    def test_alternation(self):
        self.assertTrue(test_regex("a|b", "a"))
        self.assertTrue(test_regex("a|b", "b"))
        self.assertFalse(test_regex("a|b", "c"))

    def test_star(self):
        self.assertTrue(test_regex("a*", ""))
        self.assertTrue(test_regex("a*", "aaa"))
        self.assertFalse(test_regex("a*", "b"))

    def test_plus(self):
        self.assertTrue(test_regex("a+", "a"))
        self.assertTrue(test_regex("a+", "aaa"))
        self.assertFalse(test_regex("a+", ""))

    def test_optional(self):
        self.assertTrue(test_regex("ab?", "a"))
        self.assertTrue(test_regex("ab?", "ab"))
        self.assertFalse(test_regex("ab?", "abb"))

    def test_grouping(self):
        self.assertTrue(test_regex("(ab|cd)*", "abcd"))
        self.assertTrue(test_regex("(ab|cd)*", ""))
        self.assertFalse(test_regex("(ab|cd)*", "ac"))

    def test_character_class(self):
        self.assertTrue(test_regex("[a-c]+", "abc"))
        self.assertFalse(test_regex("[a-c]+", "abd"))

    def test_digit_class(self):
        self.assertTrue(test_regex("[0-9]+", "12345"))
        self.assertFalse(test_regex("[0-9]+", "12a"))

    def test_wildcard(self):
        self.assertTrue(test_regex("a.c", "abc"))
        self.assertTrue(test_regex("a.c", "a7c"))
        self.assertFalse(test_regex("a.c", "ac"))

    def test_escaped_character(self):
        self.assertTrue(test_regex(r"a\*b", "a*b"))
        self.assertFalse(test_regex(r"a\*b", "ab"))

    def test_bounded_repetition(self):
        self.assertTrue(test_regex("a{2,4}", "aa"))
        self.assertTrue(test_regex("a{2,4}", "aaaa"))
        self.assertFalse(test_regex("a{2,4}", "a"))
        self.assertFalse(test_regex("a{2,4}", "aaaaa"))

    def test_negated_character_class(self):
        self.assertTrue(test_regex("[^0-9]+", "hello"))
        self.assertFalse(test_regex("[^0-9]+", "hello5"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
