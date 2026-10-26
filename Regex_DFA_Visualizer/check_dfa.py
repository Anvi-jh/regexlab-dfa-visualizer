
from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa
from automata_visualizer import create_dfa_diagram

print("Building NFA...")
nfa = build_simple_nfa("a.c")

print("Converting to DFA...")
dfa = convert_nfa_to_dfa(nfa)

print("Creating DFA diagram...")
graph = create_dfa_diagram(dfa)

print("Rendering DFA image...")
output = graph.render(
    filename="wildcard_dfa_test",
    directory=".",
    format="png",
    cleanup=True
)

print("DFA diagram saved to:", output)
