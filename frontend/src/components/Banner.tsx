import type { GraphData } from "../types";

export default function Banner({ data }: { data: GraphData }) {
  const root = data.nodes.find((n) => n.id === data.root_keys[0]);
  if (!root) {
    return <div className="banner ok">No stale dependencies detected.</div>;
  }
  return (
    <div className="banner">
      <b>
        {data.root_keys.length} silent {data.root_keys.length === 1 ? "dependency" : "dependencies"}
      </b>{" "}
      ({root.id}, {root.days_stale} working days) is blocking{" "}
      <b>{data.blast_count} downstream tickets</b> — milestone <b>{root.milestone}</b> due in{" "}
      <b>{root.days_to_milestone} days</b> and now at risk.
    </div>
  );
}
