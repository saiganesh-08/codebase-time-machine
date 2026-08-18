"use client";

import { useMemo } from "react";
import ReactFlow, { Background, Controls, Edge, Node } from "reactflow";
import "reactflow/dist/style.css";
import { GraphResponse } from "@/lib/api";

function riskColor(risk: number) {
  if (risk >= 66) return "#c1603f";
  if (risk >= 33) return "#e0a446";
  return "#6f9c6a";
}

export default function DependencyGraph({
  graph,
  onSelect,
}: {
  graph: GraphResponse;
  onSelect: (qname: string) => void;
}) {
  const { nodes, edges } = useMemo(() => {
    const cols = Math.ceil(Math.sqrt(graph.nodes.length || 1));
    const nodes: Node[] = graph.nodes.map((n, i) => ({
      id: n.id,
      position: { x: (i % cols) * 220, y: Math.floor(i / cols) * 110 },
      data: { label: n.id.split(".").slice(-2).join(".") },
      style: {
        background: "#1b1712",
        border: `1.5px solid ${riskColor(n.risk)}`,
        color: "#e9dfc9",
        fontSize: 11,
        fontFamily: "IBM Plex Mono, monospace",
        borderRadius: 4,
        padding: 8,
        width: 190,
      },
    }));

    const edges: Edge[] = graph.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      style: { stroke: "rgba(233,223,201,0.25)" },
      animated: false,
    }));

    return { nodes, edges };
  }, [graph]);

  return (
    <div className="panel" style={{ height: 480 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => onSelect(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(233,223,201,0.08)" gap={24} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
