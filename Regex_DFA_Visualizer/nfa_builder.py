"""Thompson NFA construction for RegexLab's deliberately limited regex syntax.

The automata use a finite alphabet: printable ASCII, ASCII whitespace, and
non-ASCII literal characters explicitly present in the pattern. This keeps the
DFA finite and the visualizer practical. Unicode literals are supported; Unicode
wide wildcard/negated-class semantics are not claimed to match Python's re.
"""
from collections import deque
import string

ASCII_UNIVERSE = frozenset(
    string.ascii_letters + string.digits + string.punctuation + " \t\r\n\v\f"
)
MAX_REGEX_LENGTH = 200
MAX_AST_NODES = 1500
MAX_NFA_STATES = 5000
MAX_REPEAT = 100


class NFA:
    def __init__(self):
        self.transitions = {}
        self.start_state = 0
        self.accept_state = 0
        self.state_count = 0

    def new_state(self):
        if self.state_count >= MAX_NFA_STATES:
            raise ValueError(
                f"This expression would exceed the safety limit of {MAX_NFA_STATES} NFA states. "
                "Simplify the expression or reduce bounded repetitions."
            )
        state = self.state_count
        self.state_count += 1
        self.transitions[state] = []
        return state

    def add_transition(self, source, chars, destination):
        # None represents epsilon; chars is a finite set of accepted symbols.
        self.transitions[source].append((chars, destination))


class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0
        self.node_count = 0
        # A finite, documented alphabet. Unicode literals in this expression
        # are included so they can be represented as ordinary DFA symbols.
        self.universe = frozenset(set(ASCII_UNIVERSE) | {
            c for c in regex if ord(c) > 127 and c not in "()|*+?{}[]\\"
        })
        self.wildcard_chars = self.universe - frozenset("\r\n")

    def peek(self, offset=0):
        index = self.pos + offset
        return self.regex[index] if index < len(self.regex) else None

    def consume(self):
        char = self.peek()
        if char is not None:
            self.pos += 1
        return char

    def node(self, kind, *values):
        self.node_count += 1
        if self.node_count > MAX_AST_NODES:
            raise ValueError(f"Expression is too complex (limit: {MAX_AST_NODES} syntax nodes).")
        return (kind, *values)

    def parse(self):
        if self.regex == "":
            raise ValueError("Regular expression cannot be empty.")
        if len(self.regex) > MAX_REGEX_LENGTH:
            raise ValueError(f"Regular expression must be at most {MAX_REGEX_LENGTH} characters long.")
        node = self.parse_alternation()
        if self.peek() is not None:
            raise ValueError(f"Unexpected character {self.peek()!r} at position {self.pos}.")
        return node

    def parse_alternation(self):
        branches = [self.parse_concatenation()]
        while self.peek() == "|":
            self.consume()
            branches.append(self.parse_concatenation())
        return branches[0] if len(branches) == 1 else self.node("alt", branches)

    def parse_concatenation(self):
        parts = []
        while self.peek() is not None and self.peek() not in ")|":
            parts.append(self.parse_repetition())
        if not parts:
            return self.node("epsilon")
        return parts[0] if len(parts) == 1 else self.node("concat", parts)

    def parse_repetition(self):
        atom = self.parse_atom()
        char = self.peek()
        if char in ("*", "+", "?"):
            self.consume()
            atom = self.node({"*": "star", "+": "plus", "?": "optional"}[char], atom)
        elif char == "{" and self.peek(1) is not None and self.peek(1).isdigit():
            atom = self.parse_bounded_repeat(atom)

        if self.peek() in ("*", "+", "?") or (
            self.peek() == "{" and self.peek(1) is not None and self.peek(1).isdigit()
        ):
            raise ValueError("Repeated quantifiers such as 'a**' or 'a+?' are not supported.")
        return atom

    def parse_bounded_repeat(self, atom):
        self.consume()  # {
        start = self.pos
        while self.peek() is not None and self.peek().isdigit():
            self.consume()
        minimum = int(self.regex[start:self.pos])
        maximum = minimum
        if self.peek() == ",":
            self.consume()
            start = self.pos
            while self.peek() is not None and self.peek().isdigit():
                self.consume()
            if start == self.pos:
                raise ValueError("Open-ended repetitions such as {2,} are not supported; use {2,4}.")
            maximum = int(self.regex[start:self.pos])
        if self.consume() != "}":
            raise ValueError("Malformed bounded repetition; expected '}'.")
        if minimum > maximum:
            raise ValueError("Repetition minimum cannot exceed its maximum.")
        if maximum > MAX_REPEAT:
            raise ValueError(f"Repetition counts must not exceed {MAX_REPEAT}.")
        parts = [atom for _ in range(minimum)]
        parts.extend(self.node("optional", atom) for _ in range(maximum - minimum))
        if not parts:
            return self.node("epsilon")
        return parts[0] if len(parts) == 1 else self.node("concat", parts)

    def parse_atom(self):
        char = self.consume()
        if char is None:
            raise ValueError("Expected an expression.")
        if char == "(":
            node = self.parse_alternation()
            if self.consume() != ")":
                raise ValueError("Missing closing parenthesis.")
            return node
        if char == "[":
            return self.node("chars", self.parse_character_class())
        if char == ".":
            return self.node("chars", self.wildcard_chars)
        if char == "\\":
            return self.node("chars", self.parse_escape())
        if char in "|*+?":
            raise ValueError(f"Unexpected operator {char!r} at position {self.pos - 1}.")
        if char in "^$":
            raise ValueError(f"Anchors {char!r} are not supported; they are not treated as literal characters.")
        # A lone closing bracket/brace is a literal outside a class. An opening
        # brace followed by digits is handled as a quantifier after an atom.
        return self.node("chars", frozenset({char}))

    def parse_escape(self):
        char = self.consume()
        if char is None:
            raise ValueError("A trailing backslash is incomplete.")
        simple = {
            "d": frozenset(string.digits),
            "w": frozenset(string.ascii_letters + string.digits + "_"),
            "s": frozenset(" \t\r\n\v\f"),
            "D": self.universe - frozenset(string.digits),
            "W": self.universe - frozenset(string.ascii_letters + string.digits + "_"),
            "S": self.universe - frozenset(" \t\r\n\v\f"),
            "n": frozenset("\n"), "t": frozenset("\t"),
            "r": frozenset("\r"), "f": frozenset("\f"), "v": frozenset("\v"),
        }
        if char in simple:
            return simple[char]
        if char in "bBAZ0123456789":
            if char in "0123456789":
                raise ValueError("Backreferences are not supported.")
            raise ValueError(f"Escape \\{char} is not supported (word boundaries and anchors are not implemented).")
        if char == "x":
            return frozenset({self._read_hex_escape(2, "\\xHH")})
        if char == "u":
            return frozenset({self._read_hex_escape(4, "\\uHHHH")})
        if char == "U":
            value = self._read_hex_value(8, "\\UHHHHHHHH")
            if value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
                raise ValueError("Unicode escape is outside the valid Unicode scalar range.")
            return frozenset({chr(value)})
        if char.isalnum():
            raise ValueError(f"Unsupported escape \\{char}. Escape punctuation to match it literally.")
        return frozenset({char})

    def _read_hex_value(self, count, notation):
        digits = ""
        for _ in range(count):
            c = self.consume()
            if c is None or c not in string.hexdigits:
                raise ValueError(f"Invalid hexadecimal escape; expected {notation}.")
            digits += c
        return int(digits, 16)

    def _read_hex_escape(self, count, notation):
        value = self._read_hex_value(count, notation)
        if 0xD800 <= value <= 0xDFFF:
            raise ValueError("Unicode escape cannot encode a surrogate code point.")
        return chr(value)

    def _class_char(self):
        char = self.consume()
        if char is None:
            raise ValueError("Missing closing ']' in character class.")
        if char != "\\":
            return char, None
        escaped = self.consume()
        if escaped is None:
            raise ValueError("Incomplete escape in character class.")
        simple = {
            "d": set(string.digits), "w": set(string.ascii_letters + string.digits + "_"),
            "s": set(" \t\r\n\v\f"), "n": {"\n"}, "t": {"\t"},
            "r": {"\r"}, "f": {"\f"}, "v": {"\v"},
            "D": set(self.universe - frozenset(string.digits)),
            "W": set(self.universe - frozenset(string.ascii_letters + string.digits + "_")),
            "S": set(self.universe - frozenset(" \t\r\n\v\f")),
        }
        if escaped in simple:
            return None, simple[escaped]
        if escaped in "bBAZ0123456789":
            raise ValueError(f"Escape \\{escaped} is not supported in character classes.")
        if escaped == "x":
            return self._read_hex_escape(2, "\\xHH"), None
        if escaped == "u":
            return self._read_hex_escape(4, "\\uHHHH"), None
        if escaped == "U":
            value = self._read_hex_value(8, "\\UHHHHHHHH")
            if value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
                raise ValueError("Unicode escape is outside the valid Unicode scalar range.")
            return chr(value), None
        if escaped.isalnum():
            raise ValueError(f"Unsupported escape \\{escaped} in character class.")
        return escaped, None

    def parse_character_class(self):
        negate = self.peek() == "^"
        if negate:
            self.consume()
        chars = set()
        first_item = True
        if self.peek() == "]":  # permit ] as the first literal in a class
            chars.add(self.consume())
            first_item = False
        while self.peek() is not None and self.peek() != "]":
            first, expanded = self._class_char()
            if expanded is not None:
                chars.update(expanded)
                first_item = False
                continue
            if (
                self.peek() == "-" and self.peek(1) is not None
                and self.peek(1) != "]"
            ):
                self.consume()
                last, last_expanded = self._class_char()
                if last is None or last_expanded is not None:
                    raise ValueError("Character ranges must have literal endpoints, such as [a-z].")
                if ord(first) > ord(last):
                    raise ValueError("Invalid character range: start exceeds end.")
                if ord(last) - ord(first) > 10000:
                    raise ValueError("Character ranges cannot exceed 10,001 code points.")
                chars.update(chr(code) for code in range(ord(first), ord(last) + 1))
            else:
                chars.add(first)
            first_item = False
        if self.consume() != "]":
            raise ValueError("Missing closing ']' in character class.")
        if not chars:
            raise ValueError("Character class cannot be empty.")
        if negate:
            chars = set(self.universe) - chars
        return frozenset(chars)


def build_simple_nfa(regex):
    """Build an epsilon-NFA with Thompson's construction and strict limits."""
    if not isinstance(regex, str):
        raise ValueError("Regular expression must be text.")
    if regex == "":
        raise ValueError("Regular expression cannot be empty.")
    if len(regex) > MAX_REGEX_LENGTH:
        raise ValueError(f"Regular expression must be at most {MAX_REGEX_LENGTH} characters long.")

    ast = RegexParser(regex).parse()
    nfa = NFA()

    def compile_node(node):
        kind = node[0]
        if kind == "epsilon":
            start, end = nfa.new_state(), nfa.new_state()
            nfa.add_transition(start, None, end)
            return start, end
        if kind == "chars":
            start, end = nfa.new_state(), nfa.new_state()
            nfa.add_transition(start, node[1], end)
            return start, end
        if kind == "concat":
            fragments = [compile_node(part) for part in node[1]]
            for (_, left_end), (right_start, _) in zip(fragments, fragments[1:]):
                nfa.add_transition(left_end, None, right_start)
            return fragments[0][0], fragments[-1][1]
        if kind == "alt":
            start, end = nfa.new_state(), nfa.new_state()
            for branch in node[1]:
                branch_start, branch_end = compile_node(branch)
                nfa.add_transition(start, None, branch_start)
                nfa.add_transition(branch_end, None, end)
            return start, end
        if kind in ("star", "plus", "optional"):
            old_start, old_end = compile_node(node[1])
            start, end = nfa.new_state(), nfa.new_state()
            nfa.add_transition(start, None, old_start)
            nfa.add_transition(old_end, None, end)
            if kind in ("star", "optional"):
                nfa.add_transition(start, None, end)
            if kind in ("star", "plus"):
                nfa.add_transition(old_end, None, old_start)
            return start, end
        raise ValueError(f"Unsupported expression node: {kind}")

    nfa.start_state, nfa.accept_state = compile_node(ast)
    return nfa
