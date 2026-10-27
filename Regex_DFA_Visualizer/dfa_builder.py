
from collections import deque
from copy import deepcopy


def epsilon_closure(nfa, states):
    """Find states reachable using epsilon transitions."""
    closure = set(states)
    stack = list(states)

    while stack:
        state = stack.pop()
        for chars, destination in nfa.transitions[state]:
            if chars is None and destination not in closure:
                closure.add(destination)
                stack.append(destination)

    return frozenset(closure)


def move(nfa, states, symbol):
    """Find states reachable after consuming one character."""
    result = set()

    for state in states:
        for chars, destination in nfa.transitions[state]:
            if chars is not None and symbol in chars:
                result.add(destination)

    return result


def convert_nfa_to_dfa(nfa, minimize=True, max_states=1000):
    """Convert an epsilon-NFA to a DFA with a strict state limit.

    Set minimize=False to inspect the direct subset-construction result.
    The returned DFA is partial; callers can complete it with a dead state.
    """
    alphabet = sorted({
        char
        for transitions in nfa.transitions.values()
        for chars, _ in transitions
        if chars is not None
        for char in chars
    })

    start = epsilon_closure(nfa, {nfa.start_state})
    dfa_states = [start]
    state_names = {start: 0}
    dfa_transitions = {}
    unprocessed = deque([start])

    while unprocessed:
        current = unprocessed.popleft()
        current_name = state_names[current]
        dfa_transitions[current_name] = {}

        for symbol in alphabet:
            reachable = move(nfa, current, symbol)
            if not reachable:
                continue

            target = epsilon_closure(nfa, reachable)

            if target not in state_names:
                if len(dfa_states) >= max_states:
                    raise ValueError(
                        f"DFA construction exceeded the safety limit of {max_states} states. "
                        "This expression is too complex to visualize safely; simplify it and try again."
                    )
                state_names[target] = len(dfa_states)
                dfa_states.append(target)
                unprocessed.append(target)

            dfa_transitions[current_name][symbol] = state_names[target]

    accept_states = {
        state_names[state]
        for state in dfa_states
        if nfa.accept_state in state
    }

    original_dfa = {
        "alphabet": alphabet,
        "states": dfa_states,
        "state_names": state_names,
        "transitions": dfa_transitions,
        "start_state": 0,
        "accept_states": accept_states,
    }

    return minimize_dfa(original_dfa) if minimize else original_dfa


def minimize_dfa(dfa):
    """Minimize a DFA using partition refinement.

    Missing transitions are treated as transitions to an implicit
    rejecting dead state. That state is omitted from the partial DFA.
    """
    alphabet = dfa["alphabet"]
    states = dfa["states"]
    transitions = dfa["transitions"]
    accepting = dfa["accept_states"]

    dead_state = len(states)
    all_states = list(range(len(states) + 1))

    complete_transitions = {}
    for state in all_states:
        complete_transitions[state] = {}
        for symbol in alphabet:
            if state == dead_state:
                destination = dead_state
            else:
                destination = transitions.get(state, {}).get(symbol, dead_state)
            complete_transitions[state][symbol] = destination

    non_accepting = [s for s in all_states if s not in accepting]
    accepting_states = [s for s in all_states if s in accepting]
    partitions = []

    if non_accepting:
        partitions.append(non_accepting)
    if accepting_states:
        partitions.append(accepting_states)

    while True:
        group_of = {
            state: index
            for index, group in enumerate(partitions)
            for state in group
        }
        refined = []

        for group in partitions:
            signatures = {}
            for state in group:
                signature = tuple(
                    group_of[complete_transitions[state][symbol]]
                    for symbol in alphabet
                )
                signatures.setdefault(signature, []).append(state)
            refined.extend(signatures.values())

        if len(refined) == len(partitions):
            partitions = refined
            break
        partitions = refined

    group_of = {
        state: index
        for index, group in enumerate(partitions)
        for state in group
    }

    dead_group = group_of[dead_state]
    start_group = group_of[dfa["start_state"]]

    ordered_groups = [start_group]
    ordered_groups.extend(
        i for i in range(len(partitions))
        if i != start_group and i != dead_group
    )
    new_id = {group: index for index, group in enumerate(ordered_groups)}

    minimized_states = []
    minimized_transitions = {}
    minimized_accepting = set()
    minimized_state_names = {}

    for group_index in ordered_groups:
        members = [
            state for state in partitions[group_index]
            if state != dead_state
        ]
        if not members:
            continue

        combined_subset = frozenset(
            nfa_state
            for state in members
            for nfa_state in states[state]
        )

        new_state = new_id[group_index]
        minimized_states.append(combined_subset)
        minimized_state_names[combined_subset] = new_state

        if any(state in accepting for state in members):
            minimized_accepting.add(new_state)

        representative = members[0]
        minimized_transitions[new_state] = {}

        for symbol in alphabet:
            destination = complete_transitions[representative][symbol]
            destination_group = group_of[destination]

            if destination_group != dead_group and destination_group in new_id:
                minimized_transitions[new_state][symbol] = new_id[destination_group]

    return {
        "alphabet": alphabet,
        "states": minimized_states,
        "state_names": minimized_state_names,
        "transitions": minimized_transitions,
        "start_state": 0,
        "accept_states": minimized_accepting,
    }


def complete_dfa(dfa):
    """Return a complete DFA over its declared alphabet.

    Missing transitions go to a rejecting dead state that loops to itself.
    If the DFA is already complete, it is returned as a copy without adding
    an unnecessary dead state.
    """
    completed = deepcopy(dfa)
    alphabet = list(completed["alphabet"])
    states = completed["states"]
    transitions = completed["transitions"]
    has_missing = any(
        symbol not in transitions.get(state, {})
        for state in range(len(states))
        for symbol in alphabet
    )
    if not has_missing:
        for state in range(len(states)):
            transitions.setdefault(state, {})
        return completed

    dead_state = len(states)
    completed["dead_state"] = dead_state
    transitions[dead_state] = {symbol: dead_state for symbol in alphabet}
    for state in range(len(states)):
        transitions.setdefault(state, {})
        for symbol in alphabet:
            transitions[state].setdefault(symbol, dead_state)
    states.append(frozenset())
    completed["state_names"] = {
        state_set: index
        for index, state_set in enumerate(states)
        if state_set
    }
    return completed
