import { Handle, Position } from "@xyflow/react";
import type { GraphNode } from "../types";

export default function TicketNode({ data }: { data: GraphNode }) {
  const kind = data.is_root ? "root" : data.in_blast ? "blast" : "healthy";
  return (
    <div className={`ticket ${kind}`}>
      <Handle type="target" position={Position.Left} />
      <div className="ticket-key">
        {data.id}
        {data.is_root && <span className="warn"> ⚠</span>}
      </div>
      <div className="ticket-sum">{data.summary}</div>
      <div className="ticket-meta">
        {data.stale ? `silent ${data.days_stale}d · ${data.owner_tz}` : data.status}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
