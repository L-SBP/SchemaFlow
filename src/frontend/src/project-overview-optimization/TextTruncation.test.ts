/**
 * Property-based tests for text truncation utilities
 * Feature: project-overview-optimization, Property 3: Project Name Truncation
 * Validates: Requirements 3.1, 3.2
 */

import * as fc from 'fast-check';
import {
  truncateText,
  truncateProjectName,
  truncateDescription,
  needsTruncation,
  descriptionNeedsTruncation,
  measureTextWidth,
  truncateToWidth
} from '../utils/project-overview';
import { PROJECT_NAME_MAX_LENGTH } from '../constants/project-overview';

describe('Text Truncation Utilities', () => {
  describe('Property 3: Project Name Truncation', () => {
    test('should truncate project names longer than 6 characters with ellipsis', () => {
      /**
       * Feature: project-overview-optimization, Property 3: Project Name Truncation
       * Validates: Requirements 3.1, 3.2
       */
      fc.assert(
        fc.property(
          fc.string({ minLength: 7, maxLength: 100 }),
          (longProjectName) => {
            const result = truncateProjectName(longProjectName);

            // Should be exactly 9 characters (6 + '...')
            expect(result).toHaveLength(9);

            // Should end with ellipsis
            expect(result.endsWith('...')).toBe(true);

            // Should start with first 6 characters of original
            expect(result.substring(0, 6)).toBe(longProjectName.substring(0, 6));
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should not truncate project names 6 characters or shorter', () => {
      /**
       * Feature: project-overview-optimization, Property 3: Project Name Truncation
       * Validates: Requirements 3.1, 3.2
       */
      fc.assert(
        fc.property(
          fc.string({ minLength: 0, maxLength: 6 }),
          (shortProjectName) => {
            const result = truncateProjectName(shortProjectName);

            // Should return original string unchanged
            expect(result).toBe(shortProjectName);

            // Should not contain ellipsis
            expect(result.includes('...')).toBe(false);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should correctly identify when truncation is needed', () => {
      /**
       * Feature: project-overview-optimization, Property 3: Project Name Truncation
       * Validates: Requirements 3.1, 3.2
       */
      fc.assert(
        fc.property(
          fc.string({ minLength: 0, maxLength: 100 }),
          (projectName) => {
            const needsTrunc = needsTruncation(projectName, PROJECT_NAME_MAX_LENGTH);
            const actuallyTruncated = truncateProjectName(projectName) !== projectName;

            // needsTruncation should match whether truncation actually occurs
            expect(needsTrunc).toBe(actuallyTruncated);

            // If length <= 6, should not need truncation
            if (projectName.length <= PROJECT_NAME_MAX_LENGTH) {
              expect(needsTrunc).toBe(false);
            } else {
              expect(needsTrunc).toBe(true);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle edge cases correctly', () => {
      // Empty string
      expect(truncateProjectName('')).toBe('');
      expect(needsTruncation('')).toBe(false);

      // Exactly 6 characters
      expect(truncateProjectName('123456')).toBe('123456');
      expect(needsTruncation('123456')).toBe(false);

      // Exactly 7 characters
      expect(truncateProjectName('1234567')).toBe('123456...');
      expect(needsTruncation('1234567')).toBe(true);
    });
  });

  describe('Description Truncation', () => {
    test('should truncate descriptions based on available width', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 50, maxLength: 200 }),
          fc.integer({ min: 100, max: 400 }),
          fc.integer({ min: 6, max: 12 }),
          (description, availableWidth, characterWidth) => {
            const result = truncateDescription(description, availableWidth, characterWidth);
            const maxChars = Math.floor(availableWidth / characterWidth);

            // If original is longer than max chars, result should be truncated
            if (description.length > maxChars) {
              expect(result.endsWith('...')).toBe(true);
              expect(result.length).toBeLessThanOrEqual(maxChars + 3); // +3 for '...'
            } else {
              expect(result).toBe(description);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should correctly identify when description truncation is needed', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 0, maxLength: 200 }),
          fc.integer({ min: 100, max: 400 }),
          fc.integer({ min: 6, max: 12 }),
          (description, availableWidth, characterWidth) => {
            const needsTrunc = descriptionNeedsTruncation(description, availableWidth, characterWidth);
            const maxChars = Math.floor(availableWidth / characterWidth);

            // Should match whether description exceeds available space
            expect(needsTrunc).toBe(description.length > maxChars);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle empty descriptions', () => {
      expect(truncateDescription('', 200)).toBe('');
      expect(descriptionNeedsTruncation('', 200)).toBe(false);
    });
  });

  describe('Text Width Measurement', () => {
    test('should return positive width for non-empty text', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.integer({ min: 10, max: 24 }),
          (text, fontSize) => {
            const width = measureTextWidth(text, fontSize);

            // Should return positive width
            expect(width).toBeGreaterThan(0);

            // Longer text should generally have greater width
            const longerText = text + 'extra';
            const longerWidth = measureTextWidth(longerText, fontSize);
            expect(longerWidth).toBeGreaterThan(width);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should return zero width for empty text', () => {
      expect(measureTextWidth('')).toBe(0);
    });
  });

  describe('Truncate to Width', () => {
    test('should truncate text to fit within specified width', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 20, maxLength: 100 }),
          fc.integer({ min: 50, max: 200 }),
          fc.integer({ min: 12, max: 18 }),
          (text, maxWidth, fontSize) => {
            const result = truncateToWidth(text, maxWidth, fontSize);
            const resultWidth = measureTextWidth(result, fontSize);

            // Result should fit within max width
            expect(resultWidth).toBeLessThanOrEqual(maxWidth);

            // If original text was too wide, result should end with ellipsis
            const originalWidth = measureTextWidth(text, fontSize);
            if (originalWidth > maxWidth) {
              expect(result.endsWith('...')).toBe(true);
            } else {
              expect(result).toBe(text);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle edge cases', () => {
      // Empty text
      expect(truncateToWidth('', 100)).toBe('');

      // Very small width should return at least ellipsis
      const result = truncateToWidth('long text', 10);
      expect(result).toBe('...');
    });
  });

  describe('Generic truncateText function', () => {
    test('should truncate at specified length with ellipsis', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 10, maxLength: 100 }),
          fc.integer({ min: 3, max: 20 }),
          (text, maxLength) => {
            const result = truncateText(text, maxLength);

            if (text.length > maxLength) {
              expect(result).toHaveLength(maxLength + 3); // +3 for '...'
              expect(result.endsWith('...')).toBe(true);
              expect(result.substring(0, maxLength)).toBe(text.substring(0, maxLength));
            } else {
              expect(result).toBe(text);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});