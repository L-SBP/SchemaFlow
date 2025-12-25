import '@testing-library/jest-dom';
import * as fc from 'fast-check';

// Configure fast-check for property-based testing
// Set default number of runs to 100 as specified in design document
fc.configureGlobal({
  numRuns: 100,
  verbose: false,
});

// Make fast-check available globally for tests
declare global {
  const fc: typeof import('fast-check');
}

(globalThis as any).fc = fc;
