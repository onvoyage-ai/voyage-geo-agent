export interface RunStorage {
  createRunDir(runId: string): Promise<string>;
  saveMetadata(runId: string, metadata: Record<string, unknown>): Promise<void>;
  loadMetadata(runId: string): Promise<Record<string, unknown>>;
  saveJSON(runId: string, filename: string, data: unknown): Promise<void>;
  loadJSON<T>(runId: string, filename: string): Promise<T>;
  saveCSV(runId: string, filename: string, data: Record<string, unknown>[]): Promise<void>;
  listRuns(): Promise<string[]>;
  getRunPath(runId: string): string;
  exists(runId: string, filename?: string): Promise<boolean>;
}
