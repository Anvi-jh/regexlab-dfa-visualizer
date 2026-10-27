
import unittest

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


def is_regex_accepted(regex, test_string):
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
        self.assertTrue(is_regex_accepted("abc", "abc"))

    def test_simple_rejection(self):
        self.assertFalse(is_regex_accepted("abc", "abd"))

    def test_alternation(self):
        self.assertTrue(is_regex_accepted("a|b", "a"))
        self.assertTrue(is_regex_accepted("a|b", "b"))
        self.assertFalse(is_regex_accepted("a|b", "c"))

    def test_star(self):
        self.assertTrue(is_regex_accepted("a*", ""))
        self.assertTrue(is_regex_accepted("a*", "aaa"))
        self.assertFalse(is_regex_accepted("a*", "b"))

    def test_plus(self):
        self.assertTrue(is_regex_accepted("a+", "a"))
        self.assertTrue(is_regex_accepted("a+", "aaa"))
        self.assertFalse(is_regex_accepted("a+", ""))

    def test_optional(self):
        self.assertTrue(is_regex_accepted("ab?", "a"))
        self.assertTrue(is_regex_accepted("ab?", "ab"))
        self.assertFalse(is_regex_accepted("ab?", "abb"))

    def test_grouping(self):
        self.assertTrue(is_regex_accepted("(ab|cd)*", "abcd"))
        self.assertTrue(is_regex_accepted("(ab|cd)*", ""))
        self.assertFalse(is_regex_accepted("(ab|cd)*", "ac"))

    def test_character_class(self):
        self.assertTrue(is_regex_accepted("[a-c]+", "abc"))
        self.assertFalse(is_regex_accepted("[a-c]+", "abd"))

    def test_digit_class(self):
        self.assertTrue(is_regex_accepted("[0-9]+", "12345"))
        self.assertFalse(is_regex_accepted("[0-9]+", "12a"))

    def test_wildcard(self):
        self.assertTrue(is_regex_accepted("a.c", "abc"))
        self.assertTrue(is_regex_accepted("a.c", "a7c"))
        self.assertFalse(is_regex_accepted("a.c", "ac"))

    def test_escaped_character(self):
        self.assertTrue(is_regex_accepted(r"a\*b", "a*b"))
        self.assertFalse(is_regex_accepted(r"a\*b", "ab"))

    def test_bounded_repetition(self):
        self.assertTrue(is_regex_accepted("a{2,4}", "aa"))
        self.assertTrue(is_regex_accepted("a{2,4}", "aaaa"))
        self.assertFalse(is_regex_accepted("a{2,4}", "a"))
        self.assertFalse(is_regex_accepted("a{2,4}", "aaaaa"))

    def test_negated_character_class(self):
        self.assertTrue(is_regex_accepted("[^0-9]+", "hello"))
        self.assertFalse(is_regex_accepted("[^0-9]+", "hello5"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
