export interface QueryResult {
  queryId: string;
  queryText: string;
  provider: string;
  model: string;
  response: string;
  latencyMs: number;
  tokenUsage?: TokenUsage;
  iteration: number;
  timestamp: string;
  error?: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface ExecutionRun {
  runId: string;
  brand: string;
  providers: string[];
  totalQueries: number;
  completedQueries: number;
  failedQueries: number;
  results: QueryResult[];
  startedAt: string;
  completedAt?: string;
  status: 'running' | 'completed' | 'failed' | 'partial';
}
