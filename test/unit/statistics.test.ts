import { describe, it, expect } from 'vitest';
import { mean, median, standardDeviation, percentage, groupBy } from '../../src/stages/analysis/statistics.js';

describe('mean', () => {
  it('should calculate average', () => {
    expect(mean([1, 2, 3, 4, 5])).toBe(3);
  });

  it('should return 0 for empty array', () => {
    expect(mean([])).toBe(0);
  });
});

describe('median', () => {
  it('should find median of odd array', () => {
    expect(median([1, 3, 5])).toBe(3);
  });

  it('should find median of even array', () => {
    expect(median([1, 2, 3, 4])).toBe(2.5);
  });

  it('should return 0 for empty array', () => {
    expect(median([])).toBe(0);
  });
});

describe('standardDeviation', () => {
  it('should calculate std dev', () => {
    const std = standardDeviation([2, 4, 4, 4, 5, 5, 7, 9]);
    expect(std).toBeCloseTo(2, 0);
  });

  it('should return 0 for empty array', () => {
    expect(standardDeviation([])).toBe(0);
  });
});

describe('percentage', () => {
  it('should calculate percentage', () => {
    expect(percentage(25, 100)).toBe(25);
  });

  it('should return 0 for zero total', () => {
    expect(percentage(5, 0)).toBe(0);
  });
});

describe('groupBy', () => {
  it('should group items by key', () => {
    const items = [
      { name: 'a', type: 'x' },
      { name: 'b', type: 'y' },
      { name: 'c', type: 'x' },
    ];
    const groups = groupBy(items, (i) => i.type);
    expect(groups.get('x')?.length).toBe(2);
    expect(groups.get('y')?.length).toBe(1);
  });
});
