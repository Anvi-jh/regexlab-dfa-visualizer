
from collections import deque
from copy import deepcopy


def epsilon_closure(nfa, states):
    """Return all states reachable through epsilon transitions."""
    closure = set(states)
    stack = list(closure)

    while stack:
        state = stack.pop()

        for chars, destination in nfa.transitions.get(state, []):
            if chars is None and destination not in closure:
                closure.add(destination)
                stack.append(destination)

    return frozenset(closure)


def move(nfa, states, symbol):
    """Return NFA states reachable by consuming symbol."""
    result = set()

    for state in states:
        for chars, destination in nfa.transitions.get(state, []):
            if chars is not None and symbol in chars:
                result.add(destination)

    return result


def convert_nfa_to_dfa(nfa, minimize=True, max_states=1000):
    """Convert an epsilon-NFA to a DFA using subset construction."""
    if max_states < 1:
        raise ValueError("max_states must be at least 1.")

    alphabet = sorted({
        symbol
        for outgoing in nfa.transitions.values()
        for chars, _ in outgoing
        if chars is not None
        for symbol in chars
    })

    start = epsilon_closure(nfa, {nfa.start_state})

    states = [start]
    state_ids = {start: 0}
    transitions = {}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        current_id = state_ids[current]
        transitions[current_id] = {}

        for symbol in alphabet:
            reachable = move(nfa, current, symbol)

            if not reachable:
                continue

            target = epsilon_closure(nfa, reachable)

            if target not in state_ids:
                if len(states) >= max_states:
                    raise ValueError(
                        f"DFA construction exceeded the safety limit "
                        f"of {max_states} states. Simplify the regex."
                    )

                state_ids[target] = len(states)
                states.append(target)
                queue.append(target)

            transitions[current_id][symbol] = state_ids[target]

    accepting = {
        state_ids[subset]
        for subset in states
        if nfa.accept_state in subset
    }

    dfa = {
        "alphabet": alphabet,
        "states": states,
        "state_names": {
            subset: index for index, subset in enumerate(states)
        },
        "transitions": transitions,
        "start_state": 0,
        "accept_states": accepting,
    }

    return minimize_dfa(dfa) if minimize else dfa


def minimize_dfa(dfa):
    """Minimize a DFA using partition refinement."""
    alphabet = list(dfa["alphabet"])
    states = list(dfa["states"])
    transitions = dfa["transitions"]
    accepting = set(dfa["accept_states"])
    start = dfa["start_state"]

    if not states:
        return {
            "alphabet": alphabet,
            "states": [],
            "state_names": {},
            "transitions": {},
            "start_state": 0,
            "accept_states": set(),
        }

    if not 0 <= start < len(states):
        raise ValueError("Invalid DFA start state.")

    if any(not 0 <= state < len(states) for state in accepting):
        raise ValueError("Invalid DFA accepting state.")

    # Remove unreachable states before minimization.
    reachable = set()
    stack = [start]

    while stack:
        state = stack.pop()

        if state in reachable:
            continue

        reachable.add(state)

        for symbol in alphabet:
            destination = transitions.get(state, {}).get(symbol)

            if destination is not None:
                if not 0 <= destination < len(states):
                    raise ValueError("Invalid DFA transition destination.")
                if destination not in reachable:
                    stack.append(destination)

    original_states = sorted(reachable)
    dead = len(states)
    all_states = original_states + [dead]

    # Complete the transition function with an implicit dead state.
    complete = {}

    for state in all_states:
        complete[state] = {}

        for symbol in alphabet:
            if state == dead:
                destination = dead
            else:
                destination = transitions.get(state, {}).get(symbol, dead)

                if destination not in reachable:
                    destination = dead

            complete[state][symbol] = destination

    non_accepting = [
        state for state in all_states if state not in accepting
    ]
    accepting_groups = [
        state for state in all_states if state in accepting
    ]

    partitions = []

    if non_accepting:
        partitions.append(non_accepting)

    if accepting_groups:
        partitions.append(accepting_groups)

    # Split groups until every state in a group has equivalent behavior.
    while True:
        group_of = {
            state: index
            for index, group in enumerate(partitions)
            for state in group
        }

        refined = []

        for group in partitions:
            buckets = {}

            for state in group:
                signature = tuple(
                    group_of[complete[state][symbol]]
                    for symbol in alphabet
                )
                buckets.setdefault(signature, []).append(state)

            refined.extend(buckets.values())

        if len(refined) == len(partitions):
            partitions = refined
            break

        partitions = refined

    group_of = {
        state: index
        for index, group in enumerate(partitions)
        for state in group
    }

    start_group = group_of[start]
    dead_group = group_of[dead]

    # Keep the start group even when the accepted language is empty.
    ordered_groups = [start_group]
    ordered_groups.extend(
        index
        for index in range(len(partitions))
        if index != start_group and index != dead_group
    )

    new_ids = {
        group_index: index
        for index, group_index in enumerate(ordered_groups)
    }

    minimized_states = []
    minimized_transitions = {}
    minimized_accepting = set()
    minimized_names = {}

    for group_index in ordered_groups:
        members = [
            state
            for state in partitions[group_index]
            if state != dead
        ]

        if not members:
            continue

        new_state = new_ids[group_index]

        # Retain NFA subsets for the visualizer.
        subset = frozenset(
            nfa_state
            for state in members
            for nfa_state in states[state]
        )

        minimized_states.append(subset)
        minimized_names[subset] = new_state

        if any(state in accepting for state in members):
            minimized_accepting.add(new_state)

        representative = members[0]
        minimized_transitions[new_state] = {}

        for symbol in alphabet:
            destination = complete[representative][symbol]
            destination_group = group_of[destination]

            # Missing transitions represent rejection in the partial DFA.
            if destination_group == dead_group:
                continue

            if destination_group in new_ids:
                minimized_transitions[new_state][symbol] = (
                    new_ids[destination_group]
                )

    return {
        "alphabet": alphabet,
        "states": minimized_states,
        "state_names": minimized_names,
        "transitions": minimized_transitions,
        "start_state": 0,
        "accept_states": minimized_accepting,
    }


def complete_dfa(dfa):
    """Return a complete DFA with an explicit dead state if required."""
    completed = deepcopy(dfa)
    alphabet = list(completed["alphabet"])
    states = completed["states"]
    transitions = completed["transitions"]

    for state in range(len(states)):
        transitions.setdefault(state, {})

    has_missing = any(
        symbol not in transitions[state]
        for state in range(len(states))
        for symbol in alphabet
    )

    if not has_missing:
        return completed

    dead = len(states)

    transitions[dead] = {
        symbol: dead for symbol in alphabet
    }

    for state in range(len(states)):
        for symbol in alphabet:
            transitions[state].setdefault(symbol, dead)

    states.append(frozenset())
    completed["dead_state"] = dead

    completed["state_names"] = {
        subset: index
        for index, subset in enumerate(states)
        if subset
    }

    return completed
