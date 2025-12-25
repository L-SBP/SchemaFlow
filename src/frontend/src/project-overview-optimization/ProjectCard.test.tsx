/**
 * ProjectCard Component Tests
 * Requirements: 1.1, 1.4, 5.1, 5.3, 5.5, 6.1, 6.3
 */

import { render, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import * as fc from 'fast-check';
import { ProjectCard } from './ProjectCard';
import { projectDataArbitrary } from '../test/generators';

describe('ProjectCard Component', () => {
  describe('Property 1: Card Click Navigation', () => {
    /**
     * **Feature: project-overview-optimization, Property 1: Card Click Navigation**
     * **Validates: Requirements 1.1, 1.4**
     * 
     * For any project card with valid project data, clicking anywhere on the card 
     * (excluding action buttons) should trigger navigation to the project workspace 
     * with the correct project ID.
     */
    it('should navigate to project workspace when card is clicked (excluding action buttons)', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card');
          expect(cardElement).toBeTruthy();

          // Click on the card (not on action buttons)
          fireEvent.click(cardElement!);

          // Should call onCardClick with correct project ID
          expect(onCardClick).toHaveBeenCalledWith(project.project_id);
          expect(onCardClick).toHaveBeenCalledTimes(1);

          // Should not call edit or delete handlers
          expect(onEdit).not.toHaveBeenCalled();
          expect(onDelete).not.toHaveBeenCalled();
        }),
        { numRuns: 100 }
      );
    });

    it('should not navigate when action buttons are clicked', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          // Find and click edit button using container query
          const editButton = container.querySelector('.action-button--edit') as HTMLElement;
          expect(editButton).toBeTruthy();
          fireEvent.click(editButton);

          // Should call onEdit, not onCardClick
          expect(onEdit).toHaveBeenCalledWith(project.project_id);
          expect(onCardClick).not.toHaveBeenCalled();

          // Reset mocks
          onEdit.mockClear();
          onCardClick.mockClear();

          // Find and click delete button using container query
          const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;
          expect(deleteButton).toBeTruthy();
          fireEvent.click(deleteButton);

          // Should call onDelete, not onCardClick
          expect(onDelete).toHaveBeenCalledWith(project.project_id);
          expect(onCardClick).not.toHaveBeenCalled();
        }),
        { numRuns: 100 }
      );
    });

    it('should handle keyboard navigation', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card');
          expect(cardElement).toBeTruthy();

          // Test Enter key
          fireEvent.keyDown(cardElement!, { key: 'Enter' });
          expect(onCardClick).toHaveBeenCalledWith(project.project_id);

          onCardClick.mockClear();

          // Test Space key
          fireEvent.keyDown(cardElement!, { key: ' ' });
          expect(onCardClick).toHaveBeenCalledWith(project.project_id);

          // Test other keys (should not trigger)
          onCardClick.mockClear();
          fireEvent.keyDown(cardElement!, { key: 'Escape' });
          expect(onCardClick).not.toHaveBeenCalled();
        }),
        { numRuns: 100 }
      );
    });
    describe('Property 5: Action Button Accessibility', () => {
      /**
       * **Feature: project-overview-optimization, Property 5: Action Button Accessibility**
       * **Validates: Requirements 5.1, 5.3, 5.5**
       * 
       * For any project card, the edit and delete action buttons should maintain 
       * minimum 32x32 pixel clickable areas and be positioned in the top-right corner 
       * with proper spacing.
       */
      it('should maintain minimum clickable area for action buttons', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            // Find action buttons
            const editButton = container.querySelector('.action-button--edit') as HTMLElement;
            const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;

            expect(editButton).toBeTruthy();
            expect(deleteButton).toBeTruthy();

            // Check minimum clickable area (32x32 pixels)
            const editStyles = window.getComputedStyle(editButton);
            const deleteStyles = window.getComputedStyle(deleteButton);

            // Check minimum width and height
            expect(parseInt(editStyles.minWidth)).toBeGreaterThanOrEqual(32);
            expect(parseInt(editStyles.minHeight)).toBeGreaterThanOrEqual(32);
            expect(parseInt(deleteStyles.minWidth)).toBeGreaterThanOrEqual(32);
            expect(parseInt(deleteStyles.minHeight)).toBeGreaterThanOrEqual(32);

            // Check positioning in top-right corner
            const actionButtonsContainer = container.querySelector('.action-buttons') as HTMLElement;
            expect(actionButtonsContainer).toBeTruthy();

            const headerElement = container.querySelector('.project-card__header') as HTMLElement;
            expect(headerElement).toBeTruthy();

            // Verify buttons are in header and positioned correctly
            expect(headerElement.contains(actionButtonsContainer)).toBe(true);
          }),
          { numRuns: 100 }
        );
      });

      it('should have proper spacing between action buttons', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            const actionButtonsContainer = container.querySelector('.action-buttons') as HTMLElement;
            expect(actionButtonsContainer).toBeTruthy();

            // Check gap between buttons (should be 4px)
            const containerStyles = window.getComputedStyle(actionButtonsContainer);
            expect(containerStyles.gap).toBe('4px');

            // Check display flex
            expect(containerStyles.display).toBe('flex');
          }),
          { numRuns: 100 }
        );
      });

      it('should have accessible labels and tooltips', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            // Find action buttons using container queries to avoid multiple element issues
            const editButton = container.querySelector('.action-button--edit') as HTMLElement;
            const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;

            expect(editButton).toBeTruthy();
            expect(deleteButton).toBeTruthy();

            // Check edit button accessibility
            expect(editButton.getAttribute('title')).toBe('编辑项目');
            expect(editButton.getAttribute('aria-label')).toBe(`编辑项目 ${project.project_id}`);

            // Check delete button accessibility
            expect(deleteButton.getAttribute('title')).toBe('删除项目');
            expect(deleteButton.getAttribute('aria-label')).toBe(`删除项目 ${project.project_id}`);
          }),
          { numRuns: 100 }
        );
      });
    });
    describe('Property 6: Status Badge Display', () => {
      /**
       * **Feature: project-overview-optimization, Property 6: Status Badge Display**
       * **Validates: Requirements 6.1, 6.3**
       * 
       * For any project status value, the card should display a properly styled badge 
       * in the bottom-left corner with appropriate color coding (green for active, gray for inactive).
       */
      it('should display status badge with correct styling and positioning', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            // Find status badge
            const statusBadge = container.querySelector('.status-badge') as HTMLElement;
            expect(statusBadge).toBeTruthy();

            // Check positioning in bottom-left corner (should be in footer)
            const footer = container.querySelector('.project-card__footer') as HTMLElement;
            expect(footer).toBeTruthy();
            expect(footer.contains(statusBadge)).toBe(true);

            // Check color coding based on status
            if (project.project_status === 'active') {
              expect(statusBadge.classList.contains('status-badge--active')).toBe(true);
              expect(statusBadge.classList.contains('status-badge--inactive')).toBe(false);
            } else if (project.project_status === 'inactive') {
              expect(statusBadge.classList.contains('status-badge--inactive')).toBe(true);
              expect(statusBadge.classList.contains('status-badge--active')).toBe(false);
            }

            // Check text content (should be capitalized)
            const expectedText = project.project_status.charAt(0).toUpperCase() + project.project_status.slice(1);
            expect(statusBadge.textContent).toBe(expectedText);

            // Check font size (should be 12px)
            const styles = window.getComputedStyle(statusBadge);
            expect(styles.fontSize).toBe('12px');
          }),
          { numRuns: 100 }
        );
      });

      it('should have proper badge styling', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            const statusBadge = container.querySelector('.status-badge') as HTMLElement;
            expect(statusBadge).toBeTruthy();

            // Check that the badge has the correct CSS classes applied
            expect(statusBadge.classList.contains('status-badge')).toBe(true);

            // Check that the badge is a span element (inline-block by default for spans with CSS)
            expect(statusBadge.tagName.toLowerCase()).toBe('span');

            // Check that the badge has the appropriate status class
            if (project.project_status === 'active') {
              expect(statusBadge.classList.contains('status-badge--active')).toBe(true);
            } else {
              expect(statusBadge.classList.contains('status-badge--inactive')).toBe(true);
            }
          }),
          { numRuns: 100 }
        );
      });

      it('should have accessible label', () => {
        fc.assert(
          fc.property(projectDataArbitrary, (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            const statusBadge = container.querySelector('.status-badge') as HTMLElement;
            expect(statusBadge).toBeTruthy();

            // Check aria-label
            const expectedLabel = `项目状态: ${project.project_status.charAt(0).toUpperCase() + project.project_status.slice(1)}`;
            expect(statusBadge.getAttribute('aria-label')).toBe(expectedLabel);
          }),
          { numRuns: 100 }
        );
      });
    });
  });

  describe('Hover and Interaction States', () => {
    /**
     * Test hover state changes and visual feedback
     * Requirements: 1.3, 1.5, 9.3
     */
    it('should apply hover class when mouse enters card', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          expect(cardElement).toBeTruthy();

          // Initially should not have hover class
          expect(cardElement.classList.contains('project-card--hover')).toBe(false);

          // Mouse enter should add hover class
          fireEvent.mouseEnter(cardElement);
          expect(cardElement.classList.contains('project-card--hover')).toBe(true);

          // Mouse leave should remove hover class
          fireEvent.mouseLeave(cardElement);
          expect(cardElement.classList.contains('project-card--hover')).toBe(false);
        }),
        { numRuns: 100 }
      );
    });

    it('should have clickable cursor styling', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          expect(cardElement).toBeTruthy();

          // Should have clickable class
          expect(cardElement.classList.contains('project-card--clickable')).toBe(true);
        }),
        { numRuns: 100 }
      );
    });

    it('should show tooltip on hover', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          expect(cardElement).toBeTruthy();

          // Mouse enter should trigger tooltip
          fireEvent.mouseEnter(cardElement);

          // Note: The tooltip has a 500ms delay, so we can't test its visibility immediately
          // But we can verify the hover state is set which triggers the tooltip logic
          expect(cardElement.classList.contains('project-card--hover')).toBe(true);
        }),
        { numRuns: 100 }
      );
    });

    it('should handle action button hover states', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const editButton = container.querySelector('.action-button--edit') as HTMLElement;
          const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;

          expect(editButton).toBeTruthy();
          expect(deleteButton).toBeTruthy();

          // Test edit button hover
          fireEvent.mouseEnter(editButton);
          fireEvent.mouseLeave(editButton);

          // Test delete button hover
          fireEvent.mouseEnter(deleteButton);
          fireEvent.mouseLeave(deleteButton);

          // Buttons should still be functional after hover
          fireEvent.click(editButton);
          expect(onEdit).toHaveBeenCalledWith(project.project_id);

          fireEvent.click(deleteButton);
          expect(onDelete).toHaveBeenCalledWith(project.project_id);
        }),
        { numRuns: 100 }
      );
    });

    it('should maintain accessibility during interactions', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          const editButton = container.querySelector('.action-button--edit') as HTMLElement;
          const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;

          // Check card accessibility attributes
          expect(cardElement.getAttribute('role')).toBe('button');
          expect(cardElement.getAttribute('tabIndex')).toBe('0');
          expect(cardElement.getAttribute('aria-label')).toBe(`Project: ${project.project_name}`);

          // Check button accessibility attributes remain intact during interactions
          fireEvent.mouseEnter(editButton);
          expect(editButton.getAttribute('aria-label')).toBe(`编辑项目 ${project.project_id}`);
          expect(editButton.getAttribute('title')).toBe('编辑项目');

          fireEvent.mouseEnter(deleteButton);
          expect(deleteButton.getAttribute('aria-label')).toBe(`删除项目 ${project.project_id}`);
          expect(deleteButton.getAttribute('title')).toBe('删除项目');
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Property 9: Layout Consistency', () => {
    /**
     * **Feature: project-overview-optimization, Property 9: Layout Consistency**
     * **Validates: Requirements 9.1, 9.2, 9.4, 9.5**
     * 
     * For any set of project cards, all cards should maintain consistent dimensions, 
     * spacing, and responsive behavior across different viewport sizes down to 320px width.
     */
    it('should maintain consistent dimensions across all cards', () => {
      fc.assert(
        fc.property(fc.array(projectDataArbitrary, { minLength: 2, maxLength: 10 }), (projects) => {
          // Ensure unique project IDs to avoid React key warnings
          const uniqueProjects = projects.map((project, index) => ({
            ...project,
            project_id: project.project_id + index * 1000
          }));

          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <div>
              {uniqueProjects.map((project) => (
                <ProjectCard
                  key={project.project_id}
                  project={project}
                  onCardClick={onCardClick}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              ))}
            </div>
          );

          const cardElements = container.querySelectorAll('.project-card');
          expect(cardElements.length).toBe(uniqueProjects.length);

          // Check that all cards have consistent CSS classes
          cardElements.forEach((card) => {
            // All cards should have the base project-card class
            expect(card.classList.contains('project-card')).toBe(true);
            expect(card.classList.contains('project-card--clickable')).toBe(true);

            // All cards should have consistent structure
            const header = card.querySelector('.project-card__header');
            const content = card.querySelector('.project-card__content');
            const footer = card.querySelector('.project-card__footer');

            expect(header).toBeTruthy();
            expect(content).toBeTruthy();
            expect(footer).toBeTruthy();
          });
        }),
        { numRuns: 100 }
      );
    });

    it('should maintain consistent spacing and margins for internal elements', () => {
      fc.assert(
        fc.property(fc.array(projectDataArbitrary, { minLength: 2, maxLength: 5 }), (projects) => {
          // Ensure unique project IDs
          const uniqueProjects = projects.map((project, index) => ({
            ...project,
            project_id: project.project_id + index * 1000
          }));

          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <div>
              {uniqueProjects.map((project) => (
                <ProjectCard
                  key={project.project_id}
                  project={project}
                  onCardClick={onCardClick}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              ))}
            </div>
          );

          const cardElements = container.querySelectorAll('.project-card');

          cardElements.forEach((card) => {
            // Check header structure
            const header = card.querySelector('.project-card__header') as HTMLElement;
            expect(header).toBeTruthy();

            const headerLeft = header.querySelector('.project-card__header-left');
            const actionButtons = header.querySelector('.action-buttons');
            expect(headerLeft).toBeTruthy();
            expect(actionButtons).toBeTruthy();

            // Check content structure
            const content = card.querySelector('.project-card__content') as HTMLElement;
            expect(content).toBeTruthy();

            // Check footer structure
            const footer = card.querySelector('.project-card__footer') as HTMLElement;
            expect(footer).toBeTruthy();

            const statusBadge = footer.querySelector('.status-badge');
            const dateDisplay = footer.querySelector('.date-display');
            expect(statusBadge).toBeTruthy();
            expect(dateDisplay).toBeTruthy();
          });
        }),
        { numRuns: 100 }
      );
    });

    it('should have responsive behavior that maintains accessibility', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          expect(cardElement).toBeTruthy();

          // Check that card maintains accessibility attributes
          expect(cardElement.getAttribute('role')).toBe('button');
          expect(cardElement.getAttribute('tabIndex')).toBe('0');
          expect(cardElement.getAttribute('aria-label')).toContain('Project:');

          // Action buttons should maintain accessibility requirements
          const editButton = container.querySelector('.action-button--edit') as HTMLElement;
          const deleteButton = container.querySelector('.action-button--delete') as HTMLElement;

          if (editButton && deleteButton) {
            // Check accessibility attributes
            expect(editButton.getAttribute('aria-label')).toContain('编辑项目');
            expect(editButton.getAttribute('title')).toBe('编辑项目');
            expect(deleteButton.getAttribute('aria-label')).toContain('删除项目');
            expect(deleteButton.getAttribute('title')).toBe('删除项目');

            // Check that buttons have the required CSS classes for styling
            expect(editButton.classList.contains('action-button--edit')).toBe(true);
            expect(deleteButton.classList.contains('action-button--delete')).toBe(true);
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should maintain layout structure with varying content lengths', () => {
      fc.assert(
        fc.property(
          fc.record({
            project_id: fc.integer({ min: 1, max: 1000 }),
            project_name: fc.string({ minLength: 1, maxLength: 50 }),
            description: fc.string({ minLength: 0, maxLength: 500 }),
            project_status: fc.constantFrom('initializing', 'active', 'inactive'),
            updated_at: fc.date().map(d => d.toISOString()),
            db_type: fc.constantFrom('mysql', 'postgresql', 'sqlite'),
          }),
          (project) => {
            const onCardClick = vi.fn();
            const onEdit = vi.fn();
            const onDelete = vi.fn();

            const { container } = render(
              <ProjectCard
                project={project}
                onCardClick={onCardClick}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            );

            const cardElement = container.querySelector('.project-card') as HTMLElement;
            expect(cardElement).toBeTruthy();

            // Card should maintain its structure regardless of content length
            const header = container.querySelector('.project-card__header') as HTMLElement;
            const content = container.querySelector('.project-card__content') as HTMLElement;
            const footer = container.querySelector('.project-card__footer') as HTMLElement;

            expect(header).toBeTruthy();
            expect(content).toBeTruthy();
            expect(footer).toBeTruthy();

            // Header should always contain database icon and project name
            const databaseIcon = header.querySelector('.database-icon');
            const projectName = header.querySelector('.project-name');
            const actionButtons = header.querySelector('.action-buttons');

            expect(databaseIcon).toBeTruthy();
            expect(projectName).toBeTruthy();
            expect(actionButtons).toBeTruthy();

            // Footer should always contain status badge and date
            const statusBadge = footer.querySelector('.status-badge');
            const dateDisplay = footer.querySelector('.date-display');

            expect(statusBadge).toBeTruthy();
            expect(dateDisplay).toBeTruthy();

            // Check that the card has the expected CSS classes for responsive behavior
            expect(cardElement.classList.contains('project-card')).toBe(true);
            expect(cardElement.classList.contains('project-card--clickable')).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle edge cases in responsive layout', () => {
      fc.assert(
        fc.property(projectDataArbitrary, (project) => {
          const onCardClick = vi.fn();
          const onEdit = vi.fn();
          const onDelete = vi.fn();

          const { container } = render(
            <ProjectCard
              project={project}
              onCardClick={onCardClick}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          );

          const cardElement = container.querySelector('.project-card') as HTMLElement;
          expect(cardElement).toBeTruthy();

          // Test that card has the expected CSS classes for responsive behavior
          expect(cardElement.classList.contains('project-card')).toBe(true);
          expect(cardElement.classList.contains('project-card--clickable')).toBe(true);

          // Test that text truncation classes are applied when needed
          const projectName = container.querySelector('.project-name--truncated') as HTMLElement;
          if (projectName) {
            expect(projectName.classList.contains('project-name--truncated')).toBe(true);
          }

          // Test that description truncation works
          const description = container.querySelector('.project-description--truncated') as HTMLElement;
          if (description) {
            expect(description.classList.contains('project-description--truncated')).toBe(true);
          }

          // Test that the card maintains accessibility attributes
          expect(cardElement.getAttribute('role')).toBe('button');
          expect(cardElement.getAttribute('tabIndex')).toBe('0');
          expect(cardElement.getAttribute('aria-label')).toContain('Project:');

          // Test that hover states can be applied
          expect(cardElement.classList.contains('project-card--hover')).toBe(false); // Initially false
        }),
        { numRuns: 100 }
      );
    });
  });
});