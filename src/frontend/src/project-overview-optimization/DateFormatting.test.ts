/**
 * Property-based tests for date formatting utilities
 * Feature: project-overview-optimization, Property 8: Date Formatting
 * Validates: Requirements 8.1, 8.5
 */

import * as fc from 'fast-check';
import { formatProjectDate } from '../utils/project-overview';

describe('Date Formatting Utilities', () => {
  describe('Property 8: Date Formatting', () => {
    test('should format valid dates in YYYY-MM-DD HH:mm format for non-today dates', () => {
      /**
       * Feature: project-overview-optimization, Property 8: Date Formatting
       * Validates: Requirements 8.1, 8.5
       */
      fc.assert(
        fc.property(
          fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })
            .filter(date => !isNaN(date.getTime())), // Filter out invalid dates
          (date) => {
            // Skip today's date for this test
            const today = new Date();
            const isToday = date.toDateString() === today.toDateString();

            if (!isToday) {
              const result = formatProjectDate(date.toISOString());

              // Should match YYYY-MM-DD HH:mm format
              const formatRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/;
              expect(result).toMatch(formatRegex);

              // Should contain correct year, month, day
              const year = date.getFullYear().toString();
              const month = (date.getMonth() + 1).toString().padStart(2, '0');
              const day = date.getDate().toString().padStart(2, '0');
              const hours = date.getHours().toString().padStart(2, '0');
              const minutes = date.getMinutes().toString().padStart(2, '0');

              const expectedFormat = `${year}-${month}-${day} ${hours}:${minutes}`;
              expect(result).toBe(expectedFormat);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format today\'s dates with "今天 HH:mm" format', () => {
      /**
       * Feature: project-overview-optimization, Property 8: Date Formatting
       * Validates: Requirements 8.1, 8.5
       */
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 23 }),
          fc.integer({ min: 0, max: 59 }),
          (hours, minutes) => {
            // Create a date for today with random time
            const today = new Date();
            today.setHours(hours, minutes, 0, 0);

            const result = formatProjectDate(today.toISOString());

            // Should match "今天 HH:mm" format
            const todayFormatRegex = /^今天 \d{2}:\d{2}$/;
            expect(result).toMatch(todayFormatRegex);

            // Should contain correct time
            const expectedHours = hours.toString().padStart(2, '0');
            const expectedMinutes = minutes.toString().padStart(2, '0');
            const expectedFormat = `今天 ${expectedHours}:${expectedMinutes}`;
            expect(result).toBe(expectedFormat);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle invalid date strings gracefully', () => {
      /**
       * Feature: project-overview-optimization, Property 8: Date Formatting
       * Validates: Requirements 8.1, 8.5
       */
      fc.assert(
        fc.property(
          fc.oneof(
            fc.string().filter(s => isNaN(Date.parse(s))), // Invalid date strings
            fc.constant(''), // Empty string
            fc.constant('invalid-date'), // Clearly invalid
            fc.constant('2023-13-45'), // Invalid month/day
            fc.constant('not-a-date') // Non-date string
          ),
          (invalidDateString) => {
            const result = formatProjectDate(invalidDateString);

            // Should return "Invalid Date" for invalid inputs
            expect(result).toBe('Invalid Date');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle edge cases correctly', () => {
      // Test specific edge cases

      // Empty string
      expect(formatProjectDate('')).toBe('Invalid Date');

      // Null/undefined (converted to string)
      expect(formatProjectDate('null')).toBe('Invalid Date');
      expect(formatProjectDate('undefined')).toBe('Invalid Date');

      // Invalid date formats
      expect(formatProjectDate('not-a-date')).toBe('Invalid Date');
      expect(formatProjectDate('2023-13-45')).toBe('Invalid Date');

      // Valid ISO string for today
      const now = new Date();
      const todayISO = now.toISOString();
      const result = formatProjectDate(todayISO);
      const expectedHours = now.getHours().toString().padStart(2, '0');
      const expectedMinutes = now.getMinutes().toString().padStart(2, '0');
      expect(result).toBe(`今天 ${expectedHours}:${expectedMinutes}`);

      // Valid ISO string for yesterday
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayISO = yesterday.toISOString();
      const yesterdayResult = formatProjectDate(yesterdayISO);

      const year = yesterday.getFullYear();
      const month = (yesterday.getMonth() + 1).toString().padStart(2, '0');
      const day = yesterday.getDate().toString().padStart(2, '0');
      const hours = yesterday.getHours().toString().padStart(2, '0');
      const minutes = yesterday.getMinutes().toString().padStart(2, '0');
      const expectedYesterday = `${year}-${month}-${day} ${hours}:${minutes}`;
      expect(yesterdayResult).toBe(expectedYesterday);
    });

    test('should consistently format the same date', () => {
      /**
       * Feature: project-overview-optimization, Property 8: Date Formatting
       * Validates: Requirements 8.1, 8.5
       */
      fc.assert(
        fc.property(
          fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })
            .filter(date => !isNaN(date.getTime())), // Filter out invalid dates
          (date) => {
            const dateString = date.toISOString();
            const result1 = formatProjectDate(dateString);
            const result2 = formatProjectDate(dateString);

            // Should return the same result for the same input
            expect(result1).toBe(result2);

            // Should not be "Invalid Date" for valid dates
            expect(result1).not.toBe('Invalid Date');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle timezone-independent formatting', () => {
      /**
       * Feature: project-overview-optimization, Property 8: Date Formatting
       * Validates: Requirements 8.1, 8.5
       */
      fc.assert(
        fc.property(
          fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })
            .filter(date => !isNaN(date.getTime())), // Filter out invalid dates
          (date) => {
            // Ensure we have a valid date before proceeding
            expect(date.getTime()).not.toBeNaN();

            // Test ISO string formatting
            const isoString = date.toISOString();
            const isoResult = formatProjectDate(isoString);

            // Should produce valid formatted dates (not "Invalid Date")
            expect(isoResult).not.toBe('Invalid Date');

            // ISO string should always produce a valid format
            if (!isoResult.startsWith('今天')) {
              const formatRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/;
              expect(isoResult).toMatch(formatRegex);
            } else {
              const todayFormatRegex = /^今天 \d{2}:\d{2}$/;
              expect(isoResult).toMatch(todayFormatRegex);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});