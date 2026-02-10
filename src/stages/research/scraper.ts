import * as cheerio from 'cheerio';
import type { ScrapedContent } from '../../types/brand.js';
import { createLogger } from '../../utils/logger.js';

const logger = createLogger('scraper');

export async function scrapeWebsite(url: string): Promise<ScrapedContent> {
  logger.info({ url }, 'Scraping website');

  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'VoyageGEO/0.1 (Brand Research Tool)',
        Accept: 'text/html',
      },
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const html = await response.text();
    const $ = cheerio.load(html);

    // Remove script and style tags
    $('script, style, nav, footer, header').remove();

    const title = $('title').text().trim();
    const metaDescription = $('meta[name="description"]').attr('content') || '';

    const headings: string[] = [];
    $('h1, h2, h3').each((_, el) => {
      const text = $(el).text().trim();
      if (text) headings.push(text);
    });

    const bodyText = $('body').text()
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 5000);

    const links: string[] = [];
    $('a[href]').each((_, el) => {
      const href = $(el).attr('href');
      if (href && href.startsWith('http')) {
        links.push(href);
      }
    });

    return {
      title,
      metaDescription,
      headings: headings.slice(0, 20),
      bodyText,
      links: [...new Set(links)].slice(0, 50),
      fetchedAt: new Date().toISOString(),
    };
  } catch (err) {
    logger.warn({ url, error: err instanceof Error ? err.message : String(err) }, 'Failed to scrape website');
    return {
      title: '',
      metaDescription: '',
      headings: [],
      bodyText: '',
      links: [],
      fetchedAt: new Date().toISOString(),
    };
  }
}
