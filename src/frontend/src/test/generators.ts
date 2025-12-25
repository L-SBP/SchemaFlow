/**
 * Property-based testing generators for project overview optimization
 * Used with fast-check for generating test data
 */

import * as fc from 'fast-check';
import { ProjectData } from '../types/project-overview';

// Generator for database types
export const dbTypeArbitrary = fc.constantFrom('mysql', 'postgresql', 'sqlite');

// Generator for project status
export const projectStatusArbitrary = fc.constantFrom('active', 'inactive');

// Generator for project IDs (positive integers)
export const projectIdArbitrary = fc.integer({ min: 1, max: 999999 });

// Generator for project names (1-50 characters)
export const projectNameArbitrary = fc.string({ minLength: 1, maxLength: 50 });

// Generator for project descriptions (0-500 characters)
export const projectDescriptionArbitrary = fc.string({ minLength: 0, maxLength: 500 });

// Generator for ISO 8601 date strings
export const isoDateArbitrary = fc.date({ min: new Date('2020-01-01T00:00:00.000Z'), max: new Date('2030-12-31T23:59:59.999Z') })
  .map(date => {
    try {
      return date.toISOString();
    } catch {
      // Fallback to a valid date if toISOString fails
      return new Date('2023-01-01T00:00:00.000Z').toISOString();
    }
  });

// Generator for valid ProjectData objects
export const projectDataArbitrary: fc.Arbitrary<ProjectData> = fc.record({
  project_id: projectIdArbitrary,
  project_name: projectNameArbitrary,
  description: projectDescriptionArbitrary,
  project_status: projectStatusArbitrary,
  updated_at: isoDateArbitrary,
  db_type: dbTypeArbitrary,
});

// Generator for arrays of ProjectData
export const projectDataArrayArbitrary = fc.array(projectDataArbitrary, { minLength: 0, maxLength: 20 });

// Generator for viewport dimensions
export const viewportDimensionsArbitrary = fc.record({
  width: fc.integer({ min: 320, max: 1920 }),
  height: fc.integer({ min: 240, max: 1080 }),
});

// Generator for tooltip positions
export const tooltipPositionArbitrary = fc.record({
  x: fc.integer({ min: 0, max: 1920 }),
  y: fc.integer({ min: 0, max: 1080 }),
  placement: fc.constantFrom('top', 'bottom', 'left', 'right'),
});

// Generator for text truncation scenarios
export const textTruncationArbitrary = fc.record({
  text: fc.string({ minLength: 0, maxLength: 100 }),
  maxLength: fc.integer({ min: 1, max: 50 }),
});

// Generator for invalid database types (for testing fallbacks)
export const invalidDbTypeArbitrary = fc.oneof(
  fc.constant(null),
  fc.constant(undefined),
  fc.string().filter(s => !['mysql', 'postgresql', 'sqlite'].includes(s))
);