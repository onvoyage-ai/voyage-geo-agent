import { describe, it, expect } from 'vitest';
import {
  truncate,
  countOccurrences,
  containsBrand,
  extractSentences,
  normalizeBrandName,
  extractBrandMentions,
  cleanResponseText,
} from '../../src/utils/text.js';

describe('truncate', () => {
  it('should not truncate short strings', () => {
    expect(truncate('hello', 10)).toBe('hello');
  });

  it('should truncate long strings with ellipsis', () => {
    expect(truncate('hello world foo', 10)).toBe('hello w...');
  });
});

describe('countOccurrences', () => {
  it('should count case-insensitive matches', () => {
    expect(countOccurrences('Notion is great. notion rocks!', 'Notion')).toBe(2);
  });

  it('should return 0 for no matches', () => {
    expect(countOccurrences('Hello world', 'Notion')).toBe(0);
  });
});

describe('containsBrand', () => {
  it('should match whole words', () => {
    expect(containsBrand('Notion is a great tool', 'Notion')).toBe(true);
  });

  it('should be case insensitive', () => {
    expect(containsBrand('I use notion daily', 'Notion')).toBe(true);
  });

  it('should not match partial words', () => {
    expect(containsBrand('The notional value', 'Notion')).toBe(false);
  });
});

describe('extractSentences', () => {
  it('should split text into sentences', () => {
    const sentences = extractSentences('Hello world. How are you? Fine!');
    expect(sentences).toEqual(['Hello world.', 'How are you?', 'Fine!']);
  });
});

describe('normalizeBrandName', () => {
  it('should lowercase and trim', () => {
    expect(normalizeBrandName('  Notion  ')).toBe('notion');
  });
});

describe('extractBrandMentions', () => {
  it('should count mentions for multiple brands', () => {
    const text = 'Notion and Confluence are great. Notion is better.';
    const mentions = extractBrandMentions(text, ['Notion', 'Confluence', 'Coda']);
    expect(mentions.get('Notion')).toBe(2);
    expect(mentions.get('Confluence')).toBe(1);
    expect(mentions.get('Coda')).toBe(0);
  });
});

describe('cleanResponseText', () => {
  it('should normalize whitespace', () => {
    expect(cleanResponseText('Hello\n\n\n\nworld  foo')).toBe('Hello\n\nworld foo');
  });
});
