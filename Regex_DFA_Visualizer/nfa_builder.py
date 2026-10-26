
import string

ASCII_UNIVERSE = frozenset(
    string.ascii_letters + string.digits + string.punctuation + " \t\r\n"
)
WILDCARD_CHARS = ASCII_UNIVERSE - frozenset("\r\n")


class NFA:
    def __init__(self):
        self.transitions = {}
        self.start_state = 0
        self.accept_state = 0
        self.state_count = 0

    def new_state(self):
        state = self.state_count
        self.state_count += 1
        self.transitions[state] = []
        return state

    def add_transition(self, source, chars, destination):
        # None represents epsilon.
        self.transitions[source].append((chars, destination))


class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    def peek(self):
        return self.regex[self.pos] if self.pos < len(self.regex) else None

    def consume(self):
        char = self.peek()
        if char is not None:
            self.pos += 1
        return char

    def parse(self):
        if not self.regex:
            raise ValueError("Regular expression cannot be empty.")

        node = self.parse_alternation()

        if self.peek() is not None:
            raise ValueError(
                f"Unexpected character {self.peek()!r} at position {self.pos}."
            )
        return node

    def parse_alternation(self):
        branches = [self.parse_concatenation()]
        while self.peek() == "|":
            self.consume()
            branches.append(self.parse_concatenation())

        return branches[0] if len(branches) == 1 else ("alt", branches)

    def parse_concatenation(self):
        parts = []
        while self.peek() is not None and self.peek() not in ")|":
            parts.append(self.parse_repetition())

        if not parts:
            return ("epsilon",)
        return parts[0] if len(parts) == 1 else ("concat", parts)

    def parse_repetition(self):
        node = self.parse_atom()

        while self.peek() in ("*", "+", "?") if self.peek() is not None else False:
            operator = self.consume()
            node = {
                "*": ("star", node),
                "+": ("plus", node),
                "?": ("optional", node),
            }[operator]

        if self.peek() == "{":
            node = self.parse_bounded_repeat(node)

        if self.peek() in ("*", "+", "?") if self.peek() is not None else False:
            raise ValueError("Repeated repetition operators are not supported.")

        return node

    def parse_bounded_repeat(self, node):
        self.consume()
        start = self.pos

        while self.peek() is not None and self.peek().isdigit():
            self.consume()

        if start == self.pos:
            raise ValueError("Expected a number after '{'.")

        minimum = int(self.regex[start:self.pos])
        maximum = minimum

        if self.peek() == ",":
            self.consume()
            start = self.pos
            while self.peek() is not None and self.peek().isdigit():
                self.consume()

            if start == self.pos:
                raise ValueError("Use a finite upper bound, such as {2,4}.")
            maximum = int(self.regex[start:self.pos])

        if self.consume() != "}":
            raise ValueError("Missing closing '}' in repetition.")
        if minimum > maximum:
            raise ValueError("Repetition minimum exceeds maximum.")
        if maximum > 100:
            raise ValueError("Repetition counts must not exceed 100.")

        parts = [node for _ in range(minimum)]
        parts.extend(("optional", node) for _ in range(maximum - minimum))

        if not parts:
            return ("epsilon",)
        return parts[0] if len(parts) == 1 else ("concat", parts)

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
            return ("chars", self.parse_character_class())
        if char == ".":
            return ("chars", WILDCARD_CHARS)
        if char == "\\":
            return ("chars", self.parse_escape())
        if char in ")|*+?{}]":
            raise ValueError(f"Unexpected operator {char!r}.")

        return ("chars", frozenset({char}))

    def parse_escape(self):
        char = self.consume()
        if char is None:
            raise ValueError("A trailing backslash is incomplete.")

        escapes = {
            "d": frozenset(string.digits),
            "w": frozenset(string.ascii_letters + string.digits + "_"),
            "s": frozenset(" \t\r\n"),
            "n": frozenset("\n"),
            "t": frozenset("\t"),
            "r": frozenset("\r"),
        }
        return escapes.get(char, frozenset({char}))

    def parse_character_class(self):
        negate = self.peek() == "^"
        if negate:
            self.consume()

        chars = set()

        while self.peek() is not None and self.peek() != "]":
            first = self.consume()

            if first == "\\":
                escaped = self.consume()
                if escaped is None:
                    raise ValueError("Incomplete escape in character class.")

                escapes = {
                    "d": set(string.digits),
                    "w": set(string.ascii_letters + string.digits + "_"),
                    "s": set(" \t\r\n"),
                    "n": {"\n"},
                    "t": {"\t"},
                    "r": {"\r"},
                }
                if escaped in escapes:
                    chars.update(escapes[escaped])
                    continue
                first = escaped

            if (
                self.peek() == "-"
                and self.pos + 1 < len(self.regex)
                and self.regex[self.pos + 1] != "]"
            ):
                self.consume()
                last = self.consume()
                if last == "\\":
                    last = self.consume()

                if last is None or ord(first) > ord(last):
                    raise ValueError("Invalid character range.")

                chars.update(chr(code) for code in range(ord(first), ord(last) + 1))
            else:
                chars.add(first)

        if self.consume() != "]":
            raise ValueError("Missing closing ']' in character class.")
        if not chars:
            raise ValueError("Character class cannot be empty.")

        if negate:
            chars = set(ASCII_UNIVERSE) - chars

        return frozenset(chars)


def build_simple_nfa(regex):
    """Build an epsilon-NFA using Thompson's construction."""
    if not regex or not regex.strip():
        raise ValueError("Regular expression cannot be empty.")

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
            for (_, left_end), (right_start, _) in zip(
                fragments, fragments[1:]
            ):
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
