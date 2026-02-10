export interface BrandProfile {
  name: string;
  website?: string;
  description: string;
  industry: string;
  category: string;
  competitors: string[];
  keywords: string[];
  uniqueSellingPoints: string[];
  targetAudience: string[];
  scrapedContent?: ScrapedContent;
}

export interface ScrapedContent {
  title: string;
  metaDescription: string;
  headings: string[];
  bodyText: string;
  links: string[];
  fetchedAt: string;
}
