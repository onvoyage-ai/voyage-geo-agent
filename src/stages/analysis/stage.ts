import type { PipelineStage } from '../types.js';
import type { RunContext } from '../../core/context.js';
import type { AnalysisResult, ExecutiveSummary } from '../../types/analysis.js';
import type { FileSystemStorage } from '../../storage/filesystem.js';
import type { Analyzer } from './analyzers/types.js';
import { MindshareAnalyzer } from './analyzers/mindshare.js';
import { MentionRateAnalyzer } from './analyzers/mention-rate.js';
import { SentimentAnalyzer } from './analyzers/sentiment.js';
import { PositioningAnalyzer } from './analyzers/positioning.js';
import { CitationAnalyzer } from './analyzers/citation.js';
import { CompetitorAnalyzer } from './analyzers/competitor.js';
import { createLogger } from '../../utils/logger.js';
import { stageHeader, createSpinner } from '../../utils/progress.js';

const logger = createLogger('analysis');

const ANALYZER_MAP: Record<string, () => Analyzer> = {
  mindshare: () => new MindshareAnalyzer(),
  'mention-rate': () => new MentionRateAnalyzer(),
  sentiment: () => new SentimentAnalyzer(),
  positioning: () => new PositioningAnalyzer(),
  citation: () => new CitationAnalyzer(),
  competitor: () => new CompetitorAnalyzer(),
};

export class AnalysisStage implements PipelineStage {
  name = 'analysis';
  description = 'Analyze AI responses for brand visibility and sentiment';

  constructor(private storage: FileSystemStorage) {}

  async execute(ctx: RunContext): Promise<RunContext> {
    stageHeader(this.name, this.description);

    if (!ctx.executionRun || !ctx.brandProfile) {
      throw new Error('Execution results and brand profile are required for analysis');
    }

    const spinner = createSpinner('Analyzing results...');
    spinner.start();

    const results = ctx.executionRun.results;
    const profile = ctx.brandProfile;
    const enabledAnalyzers = ctx.config.analysis.analyzers;

    // Run each analyzer
    const analysisData: Record<string, unknown> = {};
    for (const analyzerName of enabledAnalyzers) {
      const factory = ANALYZER_MAP[analyzerName];
      if (!factory) {
        logger.warn({ analyzer: analyzerName }, 'Unknown analyzer, skipping');
        continue;
      }

      spinner.text = `Running ${analyzerName} analyzer...`;
      const analyzer = factory();
      analysisData[analyzerName] = analyzer.analyze(results, profile);
    }

    // Generate summary
    spinner.text = 'Generating executive summary...';
    const summary = this.generateSummary(analysisData, profile.name);

    const analysisResult: AnalysisResult = {
      runId: ctx.runId,
      brand: profile.name,
      analyzedAt: new Date().toISOString(),
      mindshare: analysisData.mindshare as AnalysisResult['mindshare'],
      mentionRate: analysisData['mention-rate'] as AnalysisResult['mentionRate'],
      sentiment: analysisData.sentiment as AnalysisResult['sentiment'],
      positioning: analysisData.positioning as AnalysisResult['positioning'],
      citations: analysisData.citation as AnalysisResult['citations'],
      competitorAnalysis: analysisData.competitor as AnalysisResult['competitorAnalysis'],
      summary,
    };

    // Save analysis
    await this.storage.saveJSON(ctx.runId, 'analysis/analysis.json', analysisResult);
    await this.storage.saveJSON(ctx.runId, 'analysis/summary.json', summary);

    // Export CSVs
    await this.exportCSVs(ctx.runId, analysisResult);

    spinner.succeed('Analysis complete');
    logger.info({ brand: profile.name }, 'Analysis complete');

    return { ...ctx, analysisResult };
  }

  private generateSummary(
    data: Record<string, unknown>,
    brandName: string,
  ): ExecutiveSummary {
    const mindshare = data.mindshare as AnalysisResult['mindshare'] | undefined;
    const mentionRate = data['mention-rate'] as AnalysisResult['mentionRate'] | undefined;
    const sentiment = data.sentiment as AnalysisResult['sentiment'] | undefined;
    const positioning = data.positioning as AnalysisResult['positioning'] | undefined;
    const competitor = data.competitor as AnalysisResult['competitorAnalysis'] | undefined;

    const keyFindings: string[] = [];
    const strengths: string[] = [];
    const weaknesses: string[] = [];
    const recommendations: string[] = [];

    if (mentionRate) {
      keyFindings.push(`${brandName} is mentioned in ${mentionRate.overall}% of AI responses`);
      if (mentionRate.overall > 50) strengths.push('High mention rate across AI models');
      else if (mentionRate.overall < 20) weaknesses.push('Low mention rate in AI responses');
    }

    if (mindshare) {
      keyFindings.push(`Mindshare: ${mindshare.overall}% (rank #${mindshare.rank})`);
      if (mindshare.rank === 1) strengths.push('Leading mindshare among competitors');
    }

    if (sentiment) {
      keyFindings.push(`Sentiment: ${sentiment.label} (${sentiment.overall.toFixed(3)})`);
      if (sentiment.label === 'positive') strengths.push('Positive sentiment across AI models');
      if (sentiment.label === 'negative') weaknesses.push('Negative sentiment detected');
    }

    if (positioning) {
      keyFindings.push(`Positioned as: ${positioning.primaryPosition}`);
    }

    if (competitor && competitor.brandRank > 3) {
      weaknesses.push(`Ranked #${competitor.brandRank} among competitors`);
      recommendations.push('Increase brand visibility through content marketing');
    }

    if (mentionRate && mentionRate.overall < 30) {
      recommendations.push('Create more comparison and recommendation content');
    }

    recommendations.push('Monitor AI visibility trends over time with regular runs');

    const overallScore = Math.min(
      100,
      (mentionRate?.overall || 0) * 0.3 +
      (mindshare?.overall || 0) * 0.3 +
      (sentiment ? (sentiment.overall + 1) * 50 : 50) * 0.2 +
      (competitor ? Math.max(0, 100 - (competitor.brandRank - 1) * 20) : 50) * 0.2,
    );

    const headline = `${brandName} has ${Math.round(overallScore)}% AI visibility score`;

    return {
      headline,
      keyFindings,
      strengths,
      weaknesses,
      recommendations,
      overallScore: Math.round(overallScore),
    };
  }

  private async exportCSVs(runId: string, analysis: AnalysisResult): Promise<void> {
    // Mindshare CSV
    if (analysis.mindshare) {
      const mindshareData = Object.entries(analysis.mindshare.byProvider).map(
        ([provider, score]) => ({ provider, mindshare: score }),
      );
      if (mindshareData.length > 0) {
        await this.storage.saveCSV(runId, 'analysis/mindshare.csv', mindshareData);
      }
    }

    // Mention rates CSV
    if (analysis.mentionRate) {
      const mentionData = Object.entries(analysis.mentionRate.byProvider).map(
        ([provider, rate]) => ({ provider, mentionRate: rate }),
      );
      if (mentionData.length > 0) {
        await this.storage.saveCSV(runId, 'analysis/mention-rates.csv', mentionData);
      }
    }

    // Sentiment CSV
    if (analysis.sentiment) {
      const sentimentData = Object.entries(analysis.sentiment.byProvider).map(
        ([provider, score]) => ({ provider, sentiment: score }),
      );
      if (sentimentData.length > 0) {
        await this.storage.saveCSV(runId, 'analysis/sentiment.csv', sentimentData);
      }
    }
  }
}
