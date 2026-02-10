import { mkdir, readFile, writeFile, readdir, access } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { stringify } from 'csv-stringify/sync';
import type { RunStorage } from './types.js';
import { GeoStorageError } from '../core/errors.js';

export class FileSystemStorage implements RunStorage {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = resolve(baseDir);
  }

  getRunPath(runId: string): string {
    return join(this.baseDir, runId);
  }

  async createRunDir(runId: string): Promise<string> {
    const runDir = this.getRunPath(runId);
    await mkdir(runDir, { recursive: true });
    await mkdir(join(runDir, 'results', 'by-provider'), { recursive: true });
    await mkdir(join(runDir, 'analysis'), { recursive: true });
    await mkdir(join(runDir, 'reports', 'charts'), { recursive: true });
    return runDir;
  }

  async saveMetadata(runId: string, metadata: Record<string, unknown>): Promise<void> {
    await this.saveJSON(runId, 'metadata.json', metadata);
  }

  async loadMetadata(runId: string): Promise<Record<string, unknown>> {
    return this.loadJSON(runId, 'metadata.json');
  }

  async saveJSON(runId: string, filename: string, data: unknown): Promise<void> {
    const filePath = join(this.getRunPath(runId), filename);
    const dir = filePath.substring(0, filePath.lastIndexOf('/'));
    await mkdir(dir, { recursive: true });
    try {
      await writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');
    } catch (err) {
      throw new GeoStorageError(
        `Failed to save ${filename}: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  async loadJSON<T>(runId: string, filename: string): Promise<T> {
    const filePath = join(this.getRunPath(runId), filename);
    try {
      const content = await readFile(filePath, 'utf-8');
      return JSON.parse(content) as T;
    } catch (err) {
      throw new GeoStorageError(
        `Failed to load ${filename}: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  async saveCSV(runId: string, filename: string, data: Record<string, unknown>[]): Promise<void> {
    if (data.length === 0) return;

    const filePath = join(this.getRunPath(runId), filename);
    const dir = filePath.substring(0, filePath.lastIndexOf('/'));
    await mkdir(dir, { recursive: true });

    const columns = Object.keys(data[0]);
    const csv = stringify(data, { header: true, columns });

    try {
      await writeFile(filePath, csv, 'utf-8');
    } catch (err) {
      throw new GeoStorageError(
        `Failed to save CSV ${filename}: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  async listRuns(): Promise<string[]> {
    try {
      const entries = await readdir(this.baseDir, { withFileTypes: true });
      return entries
        .filter((e) => e.isDirectory() && e.name.startsWith('run-'))
        .map((e) => e.name)
        .sort()
        .reverse();
    } catch {
      return [];
    }
  }

  async exists(runId: string, filename?: string): Promise<boolean> {
    const filePath = filename
      ? join(this.getRunPath(runId), filename)
      : this.getRunPath(runId);
    try {
      await access(filePath);
      return true;
    } catch {
      return false;
    }
  }
}
