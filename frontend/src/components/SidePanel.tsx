import type { GraphNode } from "../types";

export default function SidePanel({ node }: { node: GraphNode | null }) {
  if (!node) {
    return (
      <aside className="side">
        <p className="hint">Select a node to inspect it.</p>
      </aside>
    );
  }
  return (
    <aside className="side">
      <h2>{node.id}</h2>
      <div className="kv"><b>Summary</b>{node.summary}</div>
      <div className="kv"><b>Status</b>{node.status}</div>
      <div className="kv">
        <b>Owner</b>
        {node.owner} <span className="muted">({node.owner_tz})</span>
      </div>
      <div className="kv"><b>Type</b>{node.dep_type.replace(/_/g, " ")}</div>
      {node.stale && <div className="kv"><b>Silent</b>{node.days_stale} working day(s)</div>}

      {node.is_root ? (
        <>
          <div className="kv">
            <b>Severity</b>
            <span className={`badge ${node.severity}`}>
              {node.severity} · {node.severity_score}
            </span>
          </div>
          {node.days_to_milestone != null && (
            <div className="kv">
              <b>Milestone</b>
              {node.milestone} · in {node.days_to_milestone}d
            </div>
          )}
          <div className="msg">{node.message}</div>
          <button className="approve">Approve &amp; send →</button>
        </>
      ) : node.in_blast ? (
        <p className="hint">
          Blocked downstream by a silent dependency. It clears once the root is unblocked.
        </p>
      ) : (
        <p className="hint">Healthy — recent activity, not blocked.</p>
      )}
    </aside>
  );
}
