import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

const WS_URL = "ws://localhost:8765";

export default function DAGDashboard() {
  const svgRef = useRef();
  const [nodes, setNodes] = useState({});
  const [links, setLinks] = useState([]);

  // -----------------------------
  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.type === "dag_event") {
        handleEvent(data);
      }
    };

    return () => ws.close();
  }, []);

  // -----------------------------
  function handleEvent(data) {
    setNodes(prev => {
      const updated = { ...prev };

      updated[data.event_hash] = {
        id: data.event_hash,
        epoch: data.epoch,
        status: data.status,
        node_id: data.node_id
      };

      return updated;
    });

    setLinks(prev => [
      ...prev,
      ...(data.parents || []).map(p => ({
        source: p,
        target: data.event_hash
      }))
    ]);
  }

  // -----------------------------
  useEffect(() => {
    renderGraph();
  }, [nodes, links]);

  // -----------------------------
  function renderGraph() {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1200;
    const height = 800;

    const nodeData = Object.values(nodes);
    // filter out duplicate links
    const linkData = Array.from(new Set(links.map(l => JSON.stringify(l)))).map(s => JSON.parse(s));

    const simulation = d3.forceSimulation(nodeData)
      .force("link", d3.forceLink(linkData).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
      .selectAll("line")
      .data(linkData)
      .enter()
      .append("line")
      .attr("stroke", "#666");

    const node = svg.append("g")
      .selectAll("circle")
      .data(nodeData)
      .enter()
      .append("circle")
      .attr("r", 8)
      .attr("fill", d => colorByStatus(d.status));

    const label = svg.append("g")
      .selectAll("text")
      .data(nodeData)
      .enter()
      .append("text")
      .text(d => d.node_id)
      .attr("font-size", 10)
      .attr("fill", "#aaa");

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      label
        .attr("x", d => d.x + 10)
        .attr("y", d => d.y);
    });
  }

  // -----------------------------
  function colorByStatus(status) {
    switch (status) {
      case "PROPOSED": return "#888";
      case "VALIDATED": return "#4da3ff";
      case "QUORUM_SATISFIED": return "#ffb347";
      case "COMMITTED": return "#2ecc71";
      case "BYZANTINE": return "#ff3b3b";
      default: return "#999";
    }
  }

  // -----------------------------
  return (
    <div style={{ background: "#0b0f14" }}>
      <svg ref={svgRef} width={1200} height={800} />
    </div>
  );
}
