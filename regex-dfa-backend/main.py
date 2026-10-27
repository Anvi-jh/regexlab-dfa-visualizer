from pathlib import Path
import sys
from collections import defaultdict
from copy import deepcopy

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Reuse the existing Python automata implementation.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTOMATA_DIR = PROJECT_ROOT / "Regex_DFA_Visualizer"
sys.path.insert(0, str(AUTOMATA_DIR))

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa


app = FastAPI(
    title="RegexLab API",
    description="API for regex-to-NFA/DFA conversion and string testing",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AutomataRequest(BaseModel):
    regex: str = Field(min_length=1, max_length=200)
    test_string: str = Field(default="", max_length=5000)


def make_complete_dfa(dfa):
    """Return a complete DFA, adding a rejecting dead state if needed."""
    completed = deepcopy(dfa)
    alphabet = list(completed["alphabet"])
    states = completed["states"]
    transitions = completed["transitions"]
    dead_state = len(states)

    has_missing_transition = any(
        symbol not in transitions.get(state, {})
        for state in range(len(states))
        for symbol in alphabet
    )

    # If every state already has every transition, no dead state is needed.
    if not has_missing_transition:
        for state in range(len(states)):
            transitions.setdefault(state, {})
            for symbol in alphabet:
                # Existing transitions are already present.
                transitions[state][symbol] = transitions[state][symbol]
        return completed

    # Record the dead state so the graph and table can identify it.
    completed["dead_state"] = dead_state

    # A dead state loops to itself for every symbol.
    transitions[dead_state] = {symbol: dead_state for symbol in alphabet}

    # Route every missing transition to the dead state.
    for state in range(len(states)):
        transitions.setdefault(state, {})
        for symbol in alphabet:
            if symbol not in transitions[state]:
                transitions[state][symbol] = dead_state

    # Keep the dead state visible in the state list and non-accepting.
    completed["states"].append(frozenset())
    completed["state_names"] = {
        state_set: index
        for index, state_set in enumerate(completed["states"])
        if state_set
    }
    return completed


def build_nfa_graph(nfa):
    """Convert the existing NFA into React Flow nodes and edges."""
    states = sorted(nfa.transitions.keys())
    nodes = []
    edges = []

    for index, state in enumerate(states):
        nodes.append({
            "id": f"q{state}",
            "type": "stateNode",
            "position": {
                "x": 80 + (index % 4) * 170,
                "y": 100 + (index // 4) * 140,
            },
            "data": {
                "label": f"q{state}",
                "accepting": state == nfa.accept_state,
                "start": state == nfa.start_state,
            },
        })

    edge_number = 0
    for source, transitions in nfa.transitions.items():
        for chars, destination in transitions:
            if chars is None:
                label = "ε"
            elif len(chars) == 1:
                label = next(iter(chars))
            elif len(chars) > 30:
                label = f"{len(chars)} characters"
            else:
                label = ", ".join(sorted(chars))

            edges.append({
                "id": f"nfa-edge-{edge_number}",
                "source": f"q{source}",
                "target": f"q{destination}",
                "label": label,
                "type": "smoothstep",
                "animated": False,
            })
            edge_number += 1

    return {"nodes": nodes, "edges": edges}


def build_dfa_graph(dfa):
    """Convert the DFA into React Flow nodes and grouped edges."""
    nodes = []

    for state in range(len(dfa["states"])):
        is_dead = bool(dfa.get("dead_state") == state)
        label = f"D{state}" + (" (dead)" if is_dead else "")
        nodes.append({
            "id": f"D{state}",
            "type": "stateNode",
            # Keep ordinary states in a horizontal row and place the
            # dead state clearly below the row so its incoming edges are visible.
            "position": (
                {"x": 300, "y": 330}
                if is_dead
                else {"x": 80 + state * 220, "y": 100}
            ),
            "data": {
                "label": label,
                "accepting": state in dfa["accept_states"],
                "start": state == dfa["start_state"],
            },
        })

    grouped_edges = defaultdict(list)

    for source, transitions in dfa["transitions"].items():
        for symbol, destination in transitions.items():
            grouped_edges[(source, destination)].append(symbol)

    edges = []
    for index, ((source, destination), symbols) in enumerate(
        grouped_edges.items()
    ):
        if len(symbols) > 12:
            label = f"{len(symbols)} characters"
        else:
            label = ", ".join(
                "ε" if symbol == "" else str(symbol)
                for symbol in sorted(symbols)
            )

        edges.append({
            "id": f"dfa-edge-{index}",
            "source": f"D{source}",
            "target": f"D{destination}",
            "label": label,
            "type": "smoothstep",
            "animated": False,
        })

    return {"nodes": nodes, "edges": edges}


def build_transition_table(dfa):
    """Create a stable table row for every DFA state, including dead states."""
    rows = []
    for state in range(len(dfa["states"])):
        transitions = dfa["transitions"].get(state, {})
        rows.append({
            "state": f"D{state}",
            "transitions": {
                repr(symbol): f"D{destination}"
                for symbol, destination in sorted(transitions.items())
            },
            "accepting": state in dfa["accept_states"],
            "dead": dfa.get("dead_state") == state,
        })
    return rows


def test_dfa_string(dfa, test_string):
    """Test a string and return its execution path and transitions."""
    current_state = dfa["start_state"]
    path = [f"D{current_state}"]
    steps = []
    rejected_early = False

    for position, character in enumerate(test_string, start=1):
        next_state = (
            dfa["transitions"]
            .get(current_state, {})
            .get(character)
        )

        steps.append({
            "position": position,
            "character": repr(character),
            "current_state": f"D{current_state}",
            "next_state": (
                f"D{next_state}" if next_state is not None else None
            ),
        })

        if next_state is None:
            rejected_early = True
            break

        current_state = next_state
        path.append(f"D{current_state}")

    accepted = (
        not rejected_early
        and current_state in dfa["accept_states"]
    )

    return {
        "input": test_string,
        "accepted": accepted,
        "path": path,
        "steps": steps,
        "final_state": (
            f"D{current_state}" if not rejected_early else None
        ),
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "RegexLab API"}


@app.post("/api/automata")
def create_automata(request: AutomataRequest):
    try:
        if not request.regex.strip():
            raise HTTPException(
                status_code=422,
                detail="Please enter a regular expression.",
            )

        nfa = build_simple_nfa(request.regex)
        dfa = convert_nfa_to_dfa(nfa)

        # RegexLab always builds a complete DFA; no partial mode is exposed.
        dfa = make_complete_dfa(dfa)

        return {
            "regex": request.regex,
            "dfa_mode": "complete",
            "nfa": build_nfa_graph(nfa),
            "dfa": build_dfa_graph(dfa),
            "transition_table": build_transition_table(dfa),
            "test": test_dfa_string(dfa, request.test_string),
        }

    except HTTPException:
        raise
    except (ValueError, SyntaxError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid regular expression: {error}",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Automata generation failed: {error}",
        ) from error
