export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface TraceInfo {
  agent_name: string;
  role: string;
  timestamp: string;
  tools_called: string[];
  handoffs: string[];
  duration_ms: number | null;
  metadata: Record<string, unknown>;
}

export interface ToolResult {
  tool: string;
  args: Record<string, unknown>;
  result: string;
}

export interface QueryResponse {
  session_id: string;
  content: string;
  module: string;
  traces: TraceInfo[];
  tool_results: ToolResult[];
  duration_ms: number;
}

export interface Module {
  name: string;
  tools: {
    name: string;
    description: string;
  }[];
}

