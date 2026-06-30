import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import rawData from "./data/graph_data.json";
import type { GraphData, GraphNode } from "./types";
import { layout, NODE_W, NODE_H } from "./layout";
import TicketNode from "./components/TicketNode";
import SidePanel from "./components/SidePanel";
import Banner from "./components/Banner";

const G = rawData as unknown as GraphData;
const nodeTypes = { ticket: TicketNode };

function miniMapColor(n: Node): string {
  const d = n.data as unknown as GraphNode;
  return d.is_root ? "#ff4d4f" : d.in_blast ? "#ff9f43" : "#2dd4a7";
}

export default function App() {
  const byId = useMemo(
    () => Object.fromEntries(G.nodes.map((n) => [n.id, n])) as Record<string, GraphNode>,
    [],
  );

  const nodes = useMemo<Node[]>(() => {
    const raw: Node[] = G.nodes.map((n) => ({
      id: n.id,
      type: "ticket",
      position: { x: 0, y: 0 },
      width: NODE_W,
      height: NODE_H,
      data: n as unknown as Record<string, unknown>,
    }));
    const edges: Edge[] = G.edges.map((e) => ({
      id: `${e.from}->${e.to}`,
      source: e.from,
      target: e.to,
    }));
    return layout(raw, edges);
  }, []);

  const edges = useMemo<Edge[]>(
    () =>
      G.edges.map((e) => {
        const fromRoot = G.root_keys.includes(e.from);
        const fromBlast = byId[e.from]?.in_blast;
        const toBlast = byId[e.to]?.in_blast;
        const hot = fromRoot || (fromBlast && toBlast);
        return {
          id: `${e.from}->${e.to}`,
          source: e.from,
          target: e.to,
          animated: fromRoot,
          className: fromRoot ? "edge-root" : hot ? "edge-hot" : "",
        };
      }),
    [byId],
  );

  const [selected, setSelected] = useState<GraphNode | null>(
    byId[G.root_keys[0]] ?? null,
  );

  const onNodeClick: NodeMouseHandler = useCallback(
    (_evt, node) => setSelected(byId[node.id] ?? null),
    [byId],
  );

  const scan = G.generated_at.replace("T", " ").replace("+00:00", " UTC");

  return (
    <div className="app">
      <header>
        <h1>Dependency Deadlock Detector</h1>
        <span className="scan">scan {scan}</span>
        <div className="legend">
          <span><i className="dot" style={{ background: "#2dd4a7" }} />healthy</span>
          <span><i className="dot" style={{ background: "#ff9f43" }} />blocked downstream</span>
          <span><i className="dot" style={{ background: "#ff4d4f" }} />silent root</span>
        </div>
      </header>

      <Banner data={G} />

      <div className="wrap">
        <div className="canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.3}
            nodesDraggable={false}
            nodesConnectable={false}
            edgesFocusable={false}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1b2740" gap={22} />
            <MiniMap
              pannable
              zoomable
              nodeColor={miniMapColor}
              maskColor="rgba(5,10,20,.6)"
              style={{ background: "#0e1626" }}
            />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <SidePanel node={selected} />
      </div>
    </div>
  );
}
