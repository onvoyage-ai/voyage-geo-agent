import type { AnalysisResult } from '../../../types/analysis.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { FileSystemStorage } from '../../../storage/filesystem.js';

export interface ReportData {
  runId: string;
  brand: BrandProfile;
  analysis: AnalysisResult;
  generatedAt: string;
}

export interface ReportRenderer {
  name: string;
  format: string;
  render(data: ReportData, storage: FileSystemStorage): Promise<string>;
}
