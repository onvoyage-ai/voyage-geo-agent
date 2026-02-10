import type { PipelineStage } from '../types.js';
import type { RunContext } from '../../core/context.js';
import type { BrandProfile } from '../../types/brand.js';
import type { ProviderRegistry } from '../../providers/registry.js';
import type { FileSystemStorage } from '../../storage/filesystem.js';
import { scrapeWebsite } from './scraper.js';
import { createLogger } from '../../utils/logger.js';
import { stageHeader, createSpinner } from '../../utils/progress.js';

const logger = createLogger('research');

export class ResearchStage implements PipelineStage {
  name = 'research';
  description = 'Research brand identity and market position';

  constructor(
    private providerRegistry: ProviderRegistry,
    private storage: FileSystemStorage,
  ) {}

  async execute(ctx: RunContext): Promise<RunContext> {
    stageHeader(this.name, this.description);

    const brandName = ctx.config.brand;
    if (!brandName) {
      throw new Error('Brand name is required for research stage');
    }

    const spinner = createSpinner('Researching brand...');
    spinner.start();

    // Scrape website if provided
    let scrapedContent;
    if (ctx.config.website) {
      spinner.text = `Scraping ${ctx.config.website}...`;
      scrapedContent = await scrapeWebsite(ctx.config.website);
    }

    // Use an AI provider for brand research
    spinner.text = 'Analyzing brand with AI...';
    const profile = await this.researchBrand(brandName, ctx.config.website, scrapedContent);

    if (scrapedContent) {
      profile.scrapedContent = scrapedContent;
    }

    // Add configured competitors
    if (ctx.config.competitors.length > 0) {
      profile.competitors = [
        ...new Set([...profile.competitors, ...ctx.config.competitors]),
      ];
    }

    await this.storage.saveJSON(ctx.runId, 'brand-profile.json', profile);
    spinner.succeed(`Brand research complete: ${profile.name}`);
    logger.info({ brand: profile.name, competitors: profile.competitors.length }, 'Research complete');

    return { ...ctx, brandProfile: profile };
  }

  private async researchBrand(
    brandName: string,
    website?: string,
    scrapedContent?: { title: string; metaDescription: string; bodyText: string },
  ): Promise<BrandProfile> {
    const providers = this.providerRegistry.getEnabled();

    if (providers.length === 0) {
      // Return a basic profile if no providers available
      return this.createBasicProfile(brandName, website);
    }

    const provider = providers[0];
    const websiteContext = scrapedContent
      ? `\nWebsite: ${website}\nTitle: ${scrapedContent.title}\nDescription: ${scrapedContent.metaDescription}\nContent excerpt: ${scrapedContent.bodyText.slice(0, 2000)}`
      : '';

    const prompt = `Analyze the brand "${brandName}" and provide a structured profile.${websiteContext}

Respond in valid JSON only (no markdown, no code fences) with this exact structure:
{
  "name": "${brandName}",
  "description": "Brief description of what the brand/product does",
  "industry": "Primary industry",
  "category": "Product category",
  "competitors": ["competitor1", "competitor2", "competitor3", "competitor4", "competitor5"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "uniqueSellingPoints": ["usp1", "usp2", "usp3"],
  "targetAudience": ["audience1", "audience2", "audience3"]
}`;

    try {
      const response = await provider.query(prompt);
      const parsed = JSON.parse(response.text) as BrandProfile;
      parsed.website = website;
      return parsed;
    } catch (err) {
      logger.warn({ error: err instanceof Error ? err.message : String(err) }, 'AI research failed, using basic profile');
      return this.createBasicProfile(brandName, website);
    }
  }

  private createBasicProfile(brandName: string, website?: string): BrandProfile {
    return {
      name: brandName,
      website,
      description: `${brandName} brand`,
      industry: 'Technology',
      category: 'Software',
      competitors: [],
      keywords: [brandName.toLowerCase()],
      uniqueSellingPoints: [],
      targetAudience: [],
    };
  }
}
