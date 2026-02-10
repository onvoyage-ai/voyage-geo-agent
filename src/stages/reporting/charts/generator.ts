import { ChartJSNodeCanvas } from 'chartjs-node-canvas';
import { writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import type { AnalysisResult } from '../../../types/analysis.js';
import { createLogger } from '../../../utils/logger.js';

const logger = createLogger('charts');

const WIDTH = 600;
const HEIGHT = 400;

let chartCanvas: ChartJSNodeCanvas | null = null;

function getCanvas(): ChartJSNodeCanvas {
  if (!chartCanvas) {
    chartCanvas = new ChartJSNodeCanvas({ width: WIDTH, height: HEIGHT, backgroundColour: '#ffffff' });
  }
  return chartCanvas;
}

export async function generateCharts(
  runDir: string,
  analysis: AnalysisResult,
): Promise<string[]> {
  const chartsDir = join(runDir, 'reports', 'charts');
  await mkdir(chartsDir, { recursive: true });

  const generated: string[] = [];

  try {
    if (analysis.mindshare?.byProvider && Object.keys(analysis.mindshare.byProvider).length > 0) {
      await generateMindshareChart(chartsDir, analysis);
      generated.push('mindshare.png');
    }

    if (analysis.sentiment?.byProvider && Object.keys(analysis.sentiment.byProvider).length > 0) {
      await generateSentimentChart(chartsDir, analysis);
      generated.push('sentiment.png');
    }

    if (analysis.mentionRate?.byProvider && Object.keys(analysis.mentionRate.byProvider).length > 0) {
      await generateMentionRateChart(chartsDir, analysis);
      generated.push('mention-rate.png');
    }

    if (analysis.competitorAnalysis?.competitors?.length > 0) {
      await generateCompetitorChart(chartsDir, analysis);
      generated.push('competitors.png');
    }
  } catch (err) {
    logger.warn({ error: err instanceof Error ? err.message : String(err) }, 'Chart generation failed');
  }

  return generated;
}

async function generateMindshareChart(dir: string, analysis: AnalysisResult): Promise<void> {
  const canvas = getCanvas();
  const providers = Object.keys(analysis.mindshare.byProvider);
  const values = Object.values(analysis.mindshare.byProvider);
  const colors = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#8b5cf6'];

  const buffer = await canvas.renderToBuffer({
    type: 'pie',
    data: {
      labels: providers,
      datasets: [{ data: values, backgroundColor: colors.slice(0, providers.length) }],
    },
    options: {
      plugins: { title: { display: true, text: 'Mindshare by Provider' } },
    },
  });

  await writeFile(join(dir, 'mindshare.png'), buffer);
}

async function generateSentimentChart(dir: string, analysis: AnalysisResult): Promise<void> {
  const canvas = getCanvas();
  const providers = Object.keys(analysis.sentiment.byProvider);
  const values = Object.values(analysis.sentiment.byProvider);

  const buffer = await canvas.renderToBuffer({
    type: 'bar',
    data: {
      labels: providers,
      datasets: [{
        label: 'Sentiment Score',
        data: values,
        backgroundColor: values.map((v) => v > 0 ? '#059669' : v < 0 ? '#dc2626' : '#d97706'),
      }],
    },
    options: {
      plugins: { title: { display: true, text: 'Sentiment by Provider' } },
      scales: { y: { suggestedMin: -1, suggestedMax: 1 } },
    },
  });

  await writeFile(join(dir, 'sentiment.png'), buffer);
}

async function generateMentionRateChart(dir: string, analysis: AnalysisResult): Promise<void> {
  const canvas = getCanvas();
  const providers = Object.keys(analysis.mentionRate.byProvider);
  const values = Object.values(analysis.mentionRate.byProvider);

  const buffer = await canvas.renderToBuffer({
    type: 'bar',
    data: {
      labels: providers,
      datasets: [{
        label: 'Mention Rate (%)',
        data: values,
        backgroundColor: '#4f46e5',
      }],
    },
    options: {
      plugins: { title: { display: true, text: 'Mention Rate by Provider' } },
      scales: { y: { suggestedMin: 0, suggestedMax: 100 } },
    },
  });

  await writeFile(join(dir, 'mention-rate.png'), buffer);
}

async function generateCompetitorChart(dir: string, analysis: AnalysisResult): Promise<void> {
  const canvas = getCanvas();
  const competitors = analysis.competitorAnalysis.competitors;
  const buffer = await canvas.renderToBuffer({
    type: 'bar',
    data: {
      labels: competitors.map((c) => c.name),
      datasets: [
        {
          label: 'Mention Rate (%)',
          data: competitors.map((c) => c.mentionRate),
          backgroundColor: '#4f46e5',
        },
        {
          label: 'Mindshare (%)',
          data: competitors.map((c) => c.mindshare),
          backgroundColor: '#059669',
        },
      ],
    },
    options: {
      plugins: { title: { display: true, text: 'Competitor Comparison' } },
      scales: { y: { suggestedMin: 0 } },
    },
  });

  await writeFile(join(dir, 'competitors.png'), buffer);
}
