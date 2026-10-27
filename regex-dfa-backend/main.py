from pathlib import Path
import logging
import sys
from typing import Literal
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Reuse the existing Python automata implementation.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTOMATA_DIR = PROJECT_ROOT / "Regex_DFA_Visualizer"
sys.path.insert(0, str(AUTOMATA_DIR))

from nfa_builder import build_simple_nfa
from dfa_builder import convert_nfa_to_dfa, complete_dfa


logger = logging.getLogger("regexlab.api")

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
    dfa_mode: Literal["complete"] = "complete"
    minimize: bool = True


def make_complete_dfa(dfa):
    """Compatibility wrapper around the shared core DFA completion helper."""
    return complete_dfa(dfa)



def arc_hint(source_pos, target_pos, step):
    """Tell the frontend whether an edge should be drawn as a curve.

    Why this exists: states are placed on a grid/row. An edge that jumps over
    a neighbour (D0 -> D2) or points backwards (D2 -> D1) would otherwise be a
    straight line hidden underneath other edges and nodes.

    Returns "above" (forward jump), "below" (any backward edge) or None
    (a normal straight edge is fine).
    """
    if source_pos["y"] != target_pos["y"]:
        return None  # different rows: the router already avoids overlap

    dx = target_pos["x"] - source_pos["x"]

    if dx == 0:
        return None  # self-loop, handled by its own edge type
    if dx < 0:
        return "below"  # backward edge
    if dx > step:
        return "above"  # forward edge that skips at least one state
    return None


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

    positions = {node["id"]: node["position"] for node in nodes}

    edge_number = 0
    for source, transitions in nfa.transitions.items():
        for chars, destination in transitions:
            if chars is None:
                label = "ε"
            elif len(chars) == 1:
                only_char = next(iter(chars))
                label = only_char if only_char.isprintable() else repr(only_char)
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
                "data": {
                    "arc": arc_hint(
                        positions[f"q{source}"],
                        positions[f"q{destination}"],
                        step=170,
                    )
                },
            })
            edge_number += 1

    return {"nodes": nodes, "edges": edges}


def build_dfa_graph(dfa):
    """Convert the DFA into React Flow nodes and grouped edges."""
    nodes = []
    dead_state = dfa.get("dead_state")
    normal_count = len(dfa["states"]) - (1 if dead_state is not None else 0)
    # Put the dead state under the middle of the row, not at a fixed x.
    dead_x = 80 + max(normal_count - 1, 0) * 220 // 2

    for state in range(len(dfa["states"])):
        is_dead = dead_state == state
        label = f"D{state}" + (" (dead)" if is_dead else "")
        nodes.append({
            "id": f"D{state}",
            "type": "stateNode",
            # Keep ordinary states in a horizontal row and place the
            # dead state clearly below the row so its incoming edges are visible.
            "position": (
                {"x": dead_x, "y": 330}
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

    positions = {node["id"]: node["position"] for node in nodes}

    edges = []
    for index, ((source, destination), symbols) in enumerate(
        grouped_edges.items()
    ):
        if len(symbols) > 12:
            label = f"{len(symbols)} characters"
        else:
            label = ", ".join(
                symbol if symbol.isprintable() else repr(symbol)
                for symbol in sorted(symbols)
            )

        edges.append({
            "id": f"dfa-edge-{index}",
            "source": f"D{source}",
            "target": f"D{destination}",
            "label": label,
            # Edges into the dead state use smooth curves so each one fans
            # out from its own source instead of sharing one "bus" line.
            "type": "default" if destination == dead_state else "smoothstep",
            "style": (
                {"strokeDasharray": "6 4", "opacity": 0.75}
                if destination == dead_state
                else {}
            ),
            "animated": False,
            "data": {
                "arc": arc_hint(
                    positions[f"D{source}"],
                    positions[f"D{destination}"],
                    step=220,
                )
            },
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
    """Run a string through the DFA and report every step.

    A complete DFA never "gets stuck": a symbol with no listed transition
    (including characters outside the regex's alphabet, like 'c' in a*b*)
    sends the machine to the dead (trap) state, where it stays forever.
    """
    alphabet = set(dfa["alphabet"])
    dead_state = dfa.get("dead_state")

    current_state = dfa["start_state"]
    path = [f"D{current_state}"]
    steps = []
    stuck = False  # only possible when there is no dead state at all

    for position, character in enumerate(test_string, start=1):
        next_state = (
            dfa["transitions"].get(current_state, {}).get(character)
        )

        if next_state is None and dead_state is not None:
            next_state = dead_state

        steps.append({
            "position": position,
            "character": repr(character),
            "current_state": f"D{current_state}",
            "next_state": (
                f"D{next_state}" if next_state is not None else None
            ),
            # Lets the UI explain *why* the string was rejected.
            "in_alphabet": character in alphabet,
        })

        if next_state is None:
            stuck = True
            break

        current_state = next_state
        path.append(f"D{current_state}")

    accepted = not stuck and current_state in dfa["accept_states"]

    return {
        "input": test_string,
        "accepted": accepted,
        "path": path,
        "steps": steps,
        "final_state": f"D{current_state}" if not stuck else None,
        "unknown_symbols": sorted(
            {repr(c) for c in test_string if c not in alphabet}
        ),
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "RegexLab API"}


@app.post("/api/automata")
def create_automata(request: AutomataRequest):
    try:
        if request.regex == "":
            raise HTTPException(
                status_code=422,
                detail="Please enter a regular expression. A single space is a valid literal pattern.",
            )

        nfa = build_simple_nfa(request.regex)
        # Subset construction is the default so students can see the direct
        # NFA-to-DFA result. Minimization remains available as an API option.
        dfa = convert_nfa_to_dfa(nfa, minimize=request.minimize, max_states=1000)

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
        # Keep implementation details in server logs, not in public responses.
        logger.exception("Unexpected error while generating automata")
        raise HTTPException(
            status_code=500,
            detail="Automata generation failed unexpectedly. Please try a simpler expression.",
        ) from error