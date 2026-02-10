import type { QueryResult } from '../types/result.js';
import type { FileSystemStorage } from './filesystem.js';

export class ResultStore {
  private storage: FileSystemStorage;
  private runId: string;
  private results: QueryResult[] = [];

  constructor(storage: FileSystemStorage, runId: string) {
    this.storage = storage;
    this.runId = runId;
  }

  async append(result: QueryResult): Promise<void> {
    this.results.push(result);
    await this.flush();
  }

  async appendBatch(results: QueryResult[]): Promise<void> {
    this.results.push(...results);
    await this.flush();
  }

  async flush(): Promise<void> {
    await this.storage.saveJSON(this.runId, 'results/results.json', this.results);

    // Group by provider
    const byProvider = new Map<string, QueryResult[]>();
    for (const result of this.results) {
      const existing = byProvider.get(result.provider) || [];
      existing.push(result);
      byProvider.set(result.provider, existing);
    }

    for (const [provider, providerResults] of byProvider) {
      await this.storage.saveJSON(
        this.runId,
        `results/by-provider/${provider}.json`,
        providerResults,
      );
    }
  }

  async load(): Promise<QueryResult[]> {
    try {
      this.results = await this.storage.loadJSON<QueryResult[]>(
        this.runId,
        'results/results.json',
      );
      return this.results;
    } catch {
      return [];
    }
  }

  getResults(): QueryResult[] {
    return [...this.results];
  }

  async exportCSV(): Promise<void> {
    const csvData = this.results.map((r) => ({
      queryId: r.queryId,
      queryText: r.queryText,
      provider: r.provider,
      model: r.model,
      latencyMs: r.latencyMs,
      iteration: r.iteration,
      timestamp: r.timestamp,
      responseLength: r.response.length,
      error: r.error || '',
    }));

    await this.storage.saveCSV(this.runId, 'results/results.csv', csvData);
  }
}
