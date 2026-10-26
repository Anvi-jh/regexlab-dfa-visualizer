
from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa
from automata_visualizer import create_nfa_diagram, create_dfa_diagram

nfa = build_simple_nfa("a(b|c)*")
dfa = convert_nfa_to_dfa(nfa)

nfa_graph = create_nfa_diagram(nfa)
dfa_graph = create_dfa_diagram(dfa)

nfa_graph.render(
    "nfa_test",
    format="png",
    cleanup=True
)

dfa_graph.render(
    "dfa_test",
    format="png",
    cleanup=True
)

print("NFA diagram created: nfa_test.png")
print("DFA diagram created: dfa_test.png")
