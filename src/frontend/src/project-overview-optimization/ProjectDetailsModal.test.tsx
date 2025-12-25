/**
 * Property-based tests for ProjectDetailsModal component
 * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
 * Validates: Requirements 7.1, 7.2, 7.3, 7.4
 */

import React from 'react';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import * as fc from 'fast-check';
import { vi } from 'vitest';
import ProjectDetailsModal from './ProjectDetailsModal';
import { projectDataArbitrary } from '../test/generators';

describe('ProjectDetailsModal Component', () => {
  beforeEach(() => {
    // Mock timers for any animations or delays
    vi.useFakeTimers();

    // Reset body overflow style
    document.body.style.overflow = 'unset';
  });

  afterEach(() => {
    vi.useRealTimers();
    cleanup();

    // Clean up body overflow style
    document.body.style.overflow = 'unset';
  });

  describe('Property 7: Description Truncation and Modal', () => {
    test('should display complete project information when modal is open', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.3, 7.4 - modal displays complete project information
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Should display modal (Requirement 7.3)
              const modal = container.querySelector('[role="dialog"]');
              expect(modal).toBeInTheDocument();
              expect(modal).toHaveAttribute('aria-modal', 'true');

              if (modal) {
                // Should display project name as title (Requirement 7.4)
                const title = modal.querySelector('#modal-title');
                expect(title).toBeInTheDocument();
                expect(title?.textContent?.trim()).toBe(project.project_name.trim());

                // Should display complete description (Requirement 7.4)
                const description = modal.querySelector('#modal-description');
                expect(description).toBeInTheDocument();
                if (project.description && project.description.trim()) {
                  expect(description?.textContent?.trim()).toBe(project.description.trim());
                } else {
                  expect(description?.textContent?.trim()).toBe('No description available');
                }

                // Should display database type (Requirement 7.4)
                const modalText = modal.textContent || '';
                const expectedDbType = project.db_type === 'mysql' ? 'MySQL' :
                  project.db_type === 'postgresql' ? 'PostgreSQL' :
                    project.db_type === 'sqlite' ? 'SQLite' : 'Unknown Database';
                expect(modalText).toContain(expectedDbType);

                // Should display project status (Requirement 7.4)
                const expectedStatus = project.project_status === 'initializing' ? '部署中' :
                  project.project_status === 'active' ? '运行中' : '非活跃';
                expect(modalText).toContain(expectedStatus);

                // Should display project ID (Requirement 7.4)
                expect(modalText).toContain(project.project_id.toString());

                // Should display formatted date (Requirement 7.4)
                const hasDateFormat = /\d{4}-\d{2}-\d{2}|\u4eca\u5929/.test(modalText);
                expect(hasDateFormat).toBe(true);
              }

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should not render when modal is closed', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.3 - modal visibility control
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={false}
                  onClose={mockOnClose}
                />
                , { container });

              // Should not display modal when closed
              const modal = container.querySelector('[role="dialog"]');
              expect(modal).not.toBeInTheDocument();

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should not render when project is null', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.3 - handle null project data
       */
      const mockOnClose = vi.fn();

      // Create a fresh container for each test iteration
      const container = document.createElement('div');
      document.body.appendChild(container);

      try {
        const { unmount } = render(
          <ProjectDetailsModal
            project={null}
            isOpen={true}
            onClose={mockOnClose}
          />
          , { container });

        // Should not display modal when project is null
        const modal = container.querySelector('[role="dialog"]');
        expect(modal).not.toBeInTheDocument();

        unmount();
      } finally {
        // Clean up container
        document.body.removeChild(container);
      }
    });

    test('should call onClose when close button is clicked', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.4 - close button dismissal
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Find and click close button
              const closeButton = container.querySelector('.modal-close-button');
              expect(closeButton).toBeInTheDocument();

              if (closeButton) {
                fireEvent.click(closeButton);
                expect(mockOnClose).toHaveBeenCalledTimes(1);
              }

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should call onClose when backdrop is clicked', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.4 - click outside dismissal
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Find modal backdrop and click it
              const modal = container.querySelector('[role="dialog"]');
              expect(modal).toBeInTheDocument();

              if (modal) {
                // Click on the backdrop (modal itself, not its content)
                fireEvent.click(modal);
                expect(mockOnClose).toHaveBeenCalledTimes(1);
              }

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should not call onClose when modal content is clicked', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.4 - prevent dismissal when clicking content
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Find modal content and click it
              const modalContent = container.querySelector('.modal-content');
              expect(modalContent).toBeInTheDocument();

              if (modalContent) {
                // Click on the modal content (should not close)
                fireEvent.click(modalContent);
                expect(mockOnClose).not.toHaveBeenCalled();
              }

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should call onClose when ESC key is pressed', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.4 - ESC key dismissal
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Simulate ESC key press
              fireEvent.keyDown(document, { key: 'Escape' });
              expect(mockOnClose).toHaveBeenCalledTimes(1);

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should not call onClose for other key presses', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.4 - only ESC key should dismiss
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          fc.constantFrom('Enter', 'Space', 'Tab', 'ArrowUp', 'ArrowDown', 'a', '1'),
          (project, key) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Simulate other key press
              fireEvent.keyDown(document, { key });
              expect(mockOnClose).not.toHaveBeenCalled();

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should prevent body scroll when modal is open', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.3 - proper modal behavior
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              // Should prevent body scroll when modal is open
              expect(document.body.style.overflow).toBe('hidden');

              unmount();

              // Should restore body scroll when modal is unmounted
              expect(document.body.style.overflow).toBe('unset');
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should have proper accessibility attributes', () => {
      /**
       * Feature: project-overview-optimization, Property 7: Description Truncation and Modal
       * Validates: Requirements 7.3 - accessibility attributes
       */
      fc.assert(
        fc.property(
          projectDataArbitrary,
          (project) => {
            const mockOnClose = vi.fn();

            // Create a fresh container for each test iteration
            const container = document.createElement('div');
            document.body.appendChild(container);

            try {
              const { unmount } = render(
                <ProjectDetailsModal
                  project={project}
                  isOpen={true}
                  onClose={mockOnClose}
                />
                , { container });

              const modal = container.querySelector('[role="dialog"]');
              expect(modal).toBeInTheDocument();

              if (modal) {
                // Should have proper ARIA attributes
                expect(modal).toHaveAttribute('role', 'dialog');
                expect(modal).toHaveAttribute('aria-modal', 'true');
                expect(modal).toHaveAttribute('aria-labelledby', 'modal-title');
                expect(modal).toHaveAttribute('aria-describedby', 'modal-description');

                // Should have title and description elements with proper IDs
                expect(modal.querySelector('#modal-title')).toBeInTheDocument();
                expect(modal.querySelector('#modal-description')).toBeInTheDocument();

                // Close button should have proper aria-label
                const closeButton = modal.querySelector('.modal-close-button');
                expect(closeButton).toHaveAttribute('aria-label', 'Close modal');
              }

              unmount();
            } finally {
              // Clean up container
              document.body.removeChild(container);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});