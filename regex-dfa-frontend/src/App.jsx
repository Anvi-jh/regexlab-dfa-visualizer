
import { useCallback, useState } from "react";
import axios from "axios";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  MarkerType,
  BaseEdge,
  EdgeLabelRenderer,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import {
  GitBranch,
  Sparkles,
  BookOpen,
  Play,
  RotateCcw,
  CheckCircle2,
  ArrowRight,
  Workflow,
  Table2,
  Code2,
  ChevronDown,
  PanelLeftClose,
  Info,
  LoaderCircle,
  XCircle,
} from "lucide-react";


import "@xyflow/react/dist/style.css";
import "./index.css";

const API_URL = "http://127.0.0.1:8000/api";

function StateNode({ data }) {
  return (
    <div className={`state-node ${data.accepting ? "accepting" : ""}`}>
      <Handle type="target" position={Position.Left} />
      {data.start && <span className="start-marker">â–¶</span>}
      <span>{data.label}</span>
      {data.accepting && <div className="accepting-ring" />}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = { stateNode: StateNode };

function cleanSymbol(symbol) {
  const value = String(symbol ?? "");
  // Backend uses Python repr(), so a single character may arrive as "'a'".
  if (value.length >= 2 && value.startsWith("'") && value.endsWith("'")) {
    return value.slice(1, -1);
  }
  return value;
}

function SelfLoopEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
  label,
  style,
}) {
  // Draw the loop above the state instead of routing an edge through the node.
  const lift = 68;
  const path = `M ${sourceX} ${sourceY} C ${sourceX + 55} ${sourceY - lift}, ${targetX - 55} ${targetY - lift}, ${targetX} ${targetY}`;

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />
      {label ? (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${(sourceX + targetX) / 2}px, ${sourceY - lift + 8}px)`,
              pointerEvents: "none",
              background: "#fffaf0",
              border: "1px solid #eadfc8",
              borderRadius: "6px",
              padding: "2px 7px",
              fontSize: "13px",
              fontWeight: 600,
              color: "#7d5555",
              whiteSpace: "nowrap",
            }}
          >
            {cleanSymbol(label)}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}

const edgeTypes = { selfLoop: SelfLoopEdge };

function graphForReactFlow(graph) {
  if (!graph) return { nodes: [], edges: [] };

  return {
    nodes: graph.nodes.map((node) => ({
      ...node,
      data: { ...node.data },
    })),
    edges: graph.edges.map((edge) => ({
      ...edge,
      type: edge.source === edge.target ? "selfLoop" : edge.type,
      label: cleanSymbol(edge.label),
      markerEnd: { type: MarkerType.ArrowClosed },
    })),
  };
}

function App() {
  const [regex, setRegex] = useState("a(b|c)*");
  const [testString, setTestString] = useState("abcb");
  const [activeGraph, setActiveGraph] = useState("DFA");
  const [showGuide, setShowGuide] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [minimizeDfa, setMinimizeDfa] = useState(false);

  const currentGraph = activeGraph === "NFA" ? result?.nfa : result?.dfa;
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const displayGraph = useCallback((graph) => {
    const converted = graphForReactFlow(graph);
    setNodes(converted.nodes);
    setEdges(converted.edges);
  }, [setNodes, setEdges]);

  const buildAutomata = async () => {
    if (regex.length === 0) {
      setError("Please enter a regular expression first.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${API_URL}/automata`, {
        regex: regex,
        test_string: testString,
        dfa_mode: "complete",
        minimize: minimizeDfa,
      });

      setResult(response.data);
      setActiveGraph("DFA");
      displayGraph(response.data.dfa);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Could not connect to the backend. Check that FastAPI is running on port 8000."
      );
      setResult(null);
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  };

  const changeGraph = (nextGraph) => {
    setActiveGraph(nextGraph);
    const graph = nextGraph === "NFA" ? result?.nfa : result?.dfa;
    displayGraph(graph);
  };

  const resetGraph = () => {
    if (currentGraph) displayGraph(currentGraph);
  };

  const clearInputs = () => {
    setRegex("");
    setTestString("");
    setError("");
    setResult(null);
    setNodes([]);
    setEdges([]);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon"><GitBranch size={23} /></div>
          <div>
            <div className="brand-name">Regex<span>Lab</span></div>
            <div className="brand-subtitle">AUTOMATA EXPLORER</div>
          </div>
        </div>

        <div className="topbar-center">
          <span className="status-dot" />
          Python backend connected
          <span className="version-chip">API</span>
        </div>

        <div className="topbar-actions">
          <button className="icon-button" title="Toggle sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <PanelLeftClose size={18} />
          </button>
          <div className="avatar">R</div>
        </div>
      </header>

      <div className="main-layout">
        {sidebarOpen && (
          <aside className="sidebar">
            <div className="section-heading">
              <div className="section-icon coral"><Code2 size={17} /></div>
              <div>
                <h2>Build automata</h2>
                <p>Define a pattern and test it</p>
              </div>
            </div>

            <label className="field-label" htmlFor="regex">Regular expression</label>
            <div className="input-wrap">
              <input
                id="regex"
                value={regex}
                maxLength={200}
                onChange={(event) => setRegex(event.target.value)}
                placeholder="e.g. a(b|c)*"
                spellCheck="false"
              />
              <span className="input-mark">.*</span>
            </div>
            <p className="field-hint">Up to 200 characters. Anchors, backreferences, lazy quantifiers, and word boundaries are not supported.</p>

            <button className="guide-toggle" onClick={() => setShowGuide(!showGuide)}>
              <BookOpen size={16} />
              Regex syntax guide
              <ChevronDown className={showGuide ? "rotate" : ""} size={16} />
            </button>

            {showGuide && (
              <div className="syntax-guide">
                <div><code>a|b</code><span>Alternation</span></div>
                <div><code>ab</code><span>Concatenation</span></div>
                <div><code>a*</code><span>Zero or more</span></div>
                <div><code>a+</code><span>One or more</span></div>
                <div><code>a?</code><span>Optional</span></div>
                <div><code>[a-z]</code><span>Character range</span></div>
                <div><code>(ab)</code><span>Grouping</span></div>
                <div><code>a{"{2,4}"}</code><span>Bounded repetition</span></div>
                <div><code>\d+</code><span>ASCII digits</span></div>
                <div><code>\D</code><span>Non-digits in the supported alphabet</span></div>
                <div><code>\w</code> / <code>\W</code><span>Word / non-word characters</span></div>
                <div><code>\s</code> / <code>\S</code><span>Whitespace / non-whitespace</span></div>
                <div><code>.</code><span>Any supported character except newline</span></div>
              </div>
            )}

            <div className="sidebar-divider" />

            <label className="field-label" htmlFor="test-string">Test string</label>
            <input
              id="test-string"
              className="text-input"
              value={testString}
              maxLength={5000}
              onChange={(event) => setTestString(event.target.value)}
              placeholder="Enter a string to test"
              spellCheck="false"
            />
            <p className="field-hint">Check whether the string matches your pattern.</p>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "9px",
                margin: "12px 0 16px",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={minimizeDfa}
                onChange={(event) => setMinimizeDfa(event.target.checked)}
              />
              Minimize DFA
            </label>

            <div className="field-hint" style={{ marginBottom: "18px" }}>
              A complete DFA is generated, including a dead state for missing transitions.
            </div>

            <button className="primary-button" onClick={buildAutomata} disabled={loading}>
              {loading ? <LoaderCircle size={17} className="spin" /> : <Play size={17} fill="currentColor" />}
              {loading ? "Building..." : "Build automata"}
              {!loading && <ArrowRight size={17} />}
            </button>

            <button className="secondary-button" onClick={clearInputs}>
              <RotateCcw size={15} />
              Clear inputs
            </button>

            <div className="sidebar-bottom">
              <div className="tip-card">
                <Sparkles size={17} />
                <div>
                  <strong>Learning tip</strong>
                  <p>Follow the states and transitions to understand how an automaton processes a string.</p>
                </div>
              </div>
              <div className="sidebar-footer">REGEXLAB Â· COMPILER DESIGN</div>
            </div>
          </aside>
        )}

        <main className="workspace">
          <div className="workspace-heading">
            <div>
              <div className="eyebrow">YOUR WORKSPACE</div>
              <h1>Automata <span>playground</span></h1>
              <p>Explore state machines and their transitions visually.</p>
            </div>
            <div className="workspace-actions">
              <span className="preview-pill">
                <span style={{ background: result ? "#71bca3" : "#e4b15d" }} />
                {result ? "Live generated data" : "Waiting for input"}
              </span>
              <button className="outline-button" onClick={resetGraph}>
                <RotateCcw size={15} /> Reset canvas
              </button>
            </div>
          </div>

          <div className={`notice-bar ${error ? "notice-error" : ""}`}>
            {error ? <XCircle size={17} /> : <Info size={17} />}
            <span>
              {error || (result
                ? `Automata generated successfully for /${result.regex}/`
                : "Enter a regex and select Build automata to generate real NFA and DFA diagrams.")}
            </span>
          </div>

          <section className="canvas-card">
            <div className="canvas-header">
              <div className="graph-tabs">
                <button
                  className={activeGraph === "NFA" ? "graph-tab active" : "graph-tab"}
                  onClick={() => changeGraph("NFA")}
                  disabled={!result}
                >
                  <Workflow size={16} /> NFA
                </button>
                <button
                  className={activeGraph === "DFA" ? "graph-tab active" : "graph-tab"}
                  onClick={() => changeGraph("DFA")}
                  disabled={!result}
                >
                  <GitBranch size={16} /> DFA
                </button>
              </div>
              <div className="canvas-tools">
                <span className="canvas-label">
                  {result ? `${activeGraph} Â· GENERATED` : "AWAITING GENERATION"}
                </span>
              </div>
            </div>

            <div className="graph-canvas">
              {nodes.length > 0 ? (
                <ReactFlow
                  key={`${activeGraph}-${result?.regex}`}
                  nodes={nodes}
                  edges={edges}
                  nodeTypes={nodeTypes}
                  edgeTypes={edgeTypes}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  fitView
                  fitViewOptions={{ padding: 0.25 }}
                  minZoom={0.2}
                  maxZoom={2}
                  nodesDraggable
                  nodesConnectable={false}
                  elementsSelectable
                  proOptions={{ hideAttribution: true }}
                >
                  <Background color="#E7DDB9" gap={22} size={1} />
                  <Controls />
                  <MiniMap
                    nodeColor={(node) => node.data?.accepting ? "#B2E3D5" : "#DE7272"}
                    maskColor="rgba(255, 245, 168, 0.5)"
                  />
                </ReactFlow>
              ) : (
                <div className="graph-placeholder">
                  <div className="empty-icon"><Workflow size={25} /></div>
                  <strong>Your automaton will appear here</strong>
                  <p>Enter a regular expression and click Build automata.</p>
                </div>
              )}
            </div>

            <div className="canvas-legend">
              <div><span className="legend-circle start-legend" /> Start state</div>
              <div><span className="legend-circle" /> Regular state</div>
              <div><span className="legend-circle accepting-legend" /> Accepting state</div>
              <div className="legend-note">Drag states Â· Scroll to zoom Â· Pan to explore</div>
            </div>
          </section>

          <div className="lower-grid">
            <section className="result-card">
              <div className="card-heading">
                <div className="card-title-icon mint"><CheckCircle2 size={17} /></div>
                <div>
                  <h3>String test result</h3>
                  <p>Execution summary</p>
                </div>
                {result && (
                  <span className={result.test.accepted ? "pending-chip accepted-chip" : "pending-chip"}>
                    {result.test.accepted ? "Accepted" : "Rejected"}
                  </span>
                )}
              </div>

              {result ? (
                <>
                  <div className={`test-outcome ${result.test.accepted ? "outcome-accepted" : "outcome-rejected"}`}>
                    {result.test.accepted ? <CheckCircle2 size={22} /> : <XCircle size={22} />}
                    <div>
                      <strong>{result.test.accepted ? "String ACCEPTED" : "String REJECTED"}</strong>
                      <p>{result.test.accepted
                        ? "The input matches the regular expression."
                        : "The input does not match the regular expression."}</p>
                    </div>
                  </div>
                  <div className="execution-path">
                    <span>EXECUTION PATH</span>
                    <code>{result.test.path.join(" â†’ ") || "No states visited"}</code>
                  </div>
                  <div className="steps-scroll">
                    <table>
                      <thead><tr><th>#</th><th>Character</th><th>From</th><th>To</th></tr></thead>
                      <tbody>
                        {result.test.steps.map((step) => (
                          <tr key={step.position}>
                            <td>{step.position}</td>
                            <td><code>{cleanSymbol(step.character)}</code></td>
                            <td>{step.current_state}</td>
                            <td>{step.next_state || "No transition"}</td>
                          </tr>
                        ))}
                        {result.test.steps.length === 0 && (
                          <tr><td colSpan="4">Empty input string</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="result-empty">
                  <div className="empty-icon"><Workflow size={22} /></div>
                  <strong>Ready to test your string</strong>
                  <p>Generate the automata to see whether your input is accepted and follow its execution path.</p>
                </div>
              )}
              <div className="execution-path">
                <span>INPUT</span>
                <code>{testString || "(empty)"}</code>
              </div>
            </section>

            <section className="table-card">
              <div className="card-heading">
                <div className="card-title-icon yellow"><Table2 size={17} /></div>
                <div>
                  <h3>DFA transition table</h3>
                  <p>
                    {result
                      ? `Complete DFA Â· Generated from your regex`
                      : "Appears after automata generation"}
                  </p>
                </div>
              </div>
              {result ? (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>State</th>
                        {Array.from(
                          new Set(
                            result.transition_table.flatMap((row) =>
                              Object.keys(row.transitions)
                            )
                          )
                        ).map((symbol) => (
                          <th key={symbol}>{cleanSymbol(symbol)}</th>
                        ))}
                        <th>Final</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.transition_table.map((row) => (
                        <tr key={row.state}>
                          <td>
                            <span className="state-code">{row.state}</span>
                            {row.dead && <span className="dead-state-tag">Dead</span>}
                          </td>
                          {Array.from(
                            new Set(
                              result.transition_table.flatMap((tableRow) =>
                                Object.keys(tableRow.transitions)
                              )
                            )
                          ).map((symbol) => (
                            <td key={symbol}>{row.transitions[symbol] ?? "â€”"}</td>
                          ))}
                          <td>{row.accepting
                            ? <span className="final-yes">Yes</span>
                            : <span className="final-no">No</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="result-empty">
                  <div className="empty-icon"><Table2 size={22} /></div>
                  <strong>No transition table yet</strong>
                  <p>Your DFA transition table will be generated by the backend.</p>
                </div>
              )}
            </section>
          </div>

          <footer className="workspace-footer">
            <span><span className="footer-dot" /> {result ? "Connected to Python API" : "Waiting for generation"}</span>
            <span>RegexLab Â· Built for learning automata</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;

