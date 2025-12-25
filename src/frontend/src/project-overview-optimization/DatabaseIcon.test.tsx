/**
 * Property-based tests for DatabaseIcon component
 * Feature: project-overview-optimization, Property 4: Database Icon Selection
 * Validates: Requirements 4.2, 4.3, 4.4, 4.6
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import DatabaseIcon from './DatabaseIcon';
import { dbTypeArbitrary, invalidDbTypeArbitrary } from '../test/generators';

describe('DatabaseIcon Component', () => {
  describe('Property 4: Database Icon Selection', () => {
    test('should display correct icon for valid database types', () => {
      /**
       * Feature: project-overview-optimization, Property 4: Database Icon Selection
       * Validates: Requirements 4.2, 4.3, 4.4, 4.6
       */
      fc.assert(
        fc.property(dbTypeArbitrary, (dbType) => {
          const { container } = render(<DatabaseIcon dbType={dbType} />);
          const img = container.querySelector('img');

          // Should render an image element
          expect(img).toBeInTheDocument();

          // Should have correct src path based on database type
          const expectedPaths = {
            mysql: '/mysql-logo.svg',
            postgresql: '/postgresql-logo.svg',
            sqlite: '/sqlite-logo.svg'
          };

          expect(img?.src).toContain(expectedPaths[dbType]);

          // Should have correct alt text
          const expectedAltTexts = {
            mysql: 'MySQL Database',
            postgresql: 'PostgreSQL Database',
            sqlite: 'SQLite Database'
          };

          expect(img?.alt).toBe(expectedAltTexts[dbType]);

          // Should have correct dimensions (Requirement 4.5)
          expect(img?.style.width).toBe('20px');
          expect(img?.style.height).toBe('20px');

          // Should have proper margin (Requirement 4.5)
          expect(img?.style.marginRight).toBe('8px');
        }),
        { numRuns: 100 }
      );
    });

    test('should display fallback icon for invalid database types', () => {
      /**
       * Feature: project-overview-optimization, Property 4: Database Icon Selection
       * Validates: Requirements 4.6
       */
      fc.assert(
        fc.property(invalidDbTypeArbitrary, (invalidDbType) => {
          // Cast to valid type for component props, but test fallback behavior
          const { container } = render(<DatabaseIcon dbType={invalidDbType as any} />);
          const img = container.querySelector('img');

          // Should render an image element
          expect(img).toBeInTheDocument();

          // Should use fallback generic database icon
          expect(img?.src).toContain('/database-logo.svg');

          // Should have generic alt text
          expect(img?.alt).toBe('Database');

          // Should still maintain correct dimensions
          expect(img?.style.width).toBe('20px');
          expect(img?.style.height).toBe('20px');
        }),
        { numRuns: 100 }
      );
    });

    test('should handle custom size prop', () => {
      fc.assert(
        fc.property(
          dbTypeArbitrary,
          fc.integer({ min: 10, max: 100 }),
          (dbType, customSize) => {
            const { container } = render(<DatabaseIcon dbType={dbType} size={customSize} />);
            const img = container.querySelector('img');

            expect(img?.style.width).toBe(`${customSize}px`);
            expect(img?.style.height).toBe(`${customSize}px`);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should apply custom className', () => {
      fc.assert(
        fc.property(
          dbTypeArbitrary,
          fc.string({ minLength: 1, maxLength: 20 }).filter(s => s.trim().length > 0),
          (dbType, customClass) => {
            const { container } = render(<DatabaseIcon dbType={dbType} className={customClass} />);
            const img = container.querySelector('img');

            // The component trims the className, so we should check for the trimmed version
            const trimmedClass = customClass.trim();
            expect(img?.className).toContain(trimmedClass);
            expect(img?.className).toContain('database-icon'); // Should also include default class
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});