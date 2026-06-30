export interface GraphNode {
  id: string;
  team: string;
  summary: string;
  owner: string;
  owner_tz: string;
  status: string;
  dep_type: string;
  stale: boolean;
  days_stale: number;
  is_root: boolean;
  in_blast: boolean;
  severity: string | null;
  severity_score: number | null;
  days_to_milestone: number | null;
  milestone: string | null;
  message: string | null;
}

export interface GraphEdge {
  from: string;
  to: string;
}

export interface GraphData {
  generated_at: string;
  drafter_label: string;
  root_keys: string[];
  blast_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
