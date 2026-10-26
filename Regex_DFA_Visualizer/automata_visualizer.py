from graphviz import Digraph


def create_nfa_diagram(nfa):
    graph = Digraph("NFA")
    graph.attr(rankdir="LR", size="14,8")
    graph.attr("node", shape="circle")
    graph.node("start", label="", shape="none", width="0")
    graph.edge("start", str(nfa.start_state))

    for state in nfa.transitions:
        shape = "doublecircle" if state == nfa.accept_state else "circle"
        graph.node(str(state), shape=shape)

    for source, transitions in nfa.transitions.items():
        for chars, destination in transitions:
            if chars is None:
                label = "ε"
            elif len(chars) > 40:
                label = f"Any of {len(chars)} characters"
            elif len(chars) == 1:
                label = next(iter(chars))
            else:
                label = "[" + "".join(sorted(chars)) + "]"

            graph.edge(str(source), str(destination), label=label)

    return graph


def create_dfa_diagram(dfa):
    graph = Digraph("DFA")
    graph.attr(rankdir="LR", size="14,8")
    graph.attr("node", shape="circle")
    graph.node("start", label="", shape="none", width="0")
    graph.edge("start", f"D{dfa['start_state']}")

    for state in range(len(dfa["states"])):
        shape = "doublecircle" if state in dfa["accept_states"] else "circle"
        graph.node(f"D{state}", shape=shape)

    for source, transitions in dfa["transitions"].items():
        grouped = {}
        for symbol, destination in transitions.items():
            grouped.setdefault(destination, []).append(symbol)

        for destination, symbols in grouped.items():
            label = (
                f"{len(symbols)} characters"
                if len(symbols) > 20
                else ", ".join(repr(s) for s in sorted(symbols))
            )
            graph.edge(f"D{source}", f"D{destination}", label=label)

    return graph
