/**
 * Integration tests for ProjectOverview component
 * Requirements: All requirements integration
 * 
 * Tests complete project overview functionality and error conditions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import ProjectOverview from './ProjectOverview';
import { ProjectData } from '../types/project-overview';

// Mock project data for testing
const mockValidProjects: ProjectData[] = [
  {
    project_id: 1,
    project_name: 'Test Project 1',
    description: 'This is a test project description',
    project_status: 'active',
    updated_at: '2023-12-01T10:00:00Z',
    db_type: 'mysql'
  },
  {
    project_id: 2,
    project_name: 'Another Project',
    description: 'Another test project with a longer description that might need truncation',
    project_status: 'inactive',
    updated_at: '2023-12-02T15:30:00Z',
    db_type: 'postgresql'
  }
];

const mockInvalidProjects = [
  {
    project_id: 1,
    project_name: 'Valid Project',
    description: 'Valid description',
    project_status: 'active',
    updated_at: '2023-12-01T10:00:00Z',
    db_type: 'mysql'
  },
  {
    // Missing required fields
    project_id: null,
    project_name: '',
    description: null,
    project_status: 'unknown',
    updated_at: 'invalid-date',
    db_type: 'unknown'
  },
  {
    // Invalid types
    project_id: 'not-a-number',
    project_name: 123,
    description: {},
    project_status: 'invalid-status',
    updated_at: null,
    db_type: 'invalid-db'
  }
];

describe('ProjectOverview Integration Tests', () => {
  // Mock handlers
  const mockOnCardClick = vi.fn();
  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnRefresh = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    test('should display loading state when loading is true', () => {
      render(
        <ProjectOverview
          projects={[]}
          loading={true}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Loading projects...')).toBeInTheDocument();
      expect(screen.getByLabelText('Loading projects...')).toBeInTheDocument();
      // Just check that the loading spinner is present
      expect(document.querySelector('.spinner')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('should display error state when error is provided', () => {
      const errorMessage = 'Failed to load projects from server';

      render(
        <ProjectOverview
          projects={[]}
          error={errorMessage}
          onRefresh={mockOnRefresh}
        />
      );

      expect(screen.getByText('Failed to load projects')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
    });

    test('should call onRefresh when retry button is clicked', () => {
      render(
        <ProjectOverview
          projects={[]}
          error="Network error"
          onRefresh={mockOnRefresh}
        />
      );

      const retryButton = screen.getByRole('button', { name: 'Try Again' });
      fireEvent.click(retryButton);

      expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });

    test('should not show retry button when onRefresh is not provided', () => {
      render(
        <ProjectOverview
          projects={[]}
          error="Network error"
        />
      );

      expect(screen.queryByRole('button', { name: 'Try Again' })).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('should display empty state when no projects are provided', () => {
      render(
        <ProjectOverview
          projects={[]}
          onRefresh={mockOnRefresh}
        />
      );

      expect(screen.getByText('No projects found')).toBeInTheDocument();
      expect(screen.getByText('You don\'t have any projects yet.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    });

    test('should call onRefresh when refresh button is clicked in empty state', () => {
      render(
        <ProjectOverview
          projects={[]}
          onRefresh={mockOnRefresh}
        />
      );

      const refreshButton = screen.getByRole('button', { name: 'Refresh' });
      fireEvent.click(refreshButton);

      expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Success State with Valid Projects', () => {
    test('should render project cards when valid projects are provided', () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Check that project cards are rendered (use aria-label since text is truncated)
      expect(screen.getByLabelText('Project: Test Project 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Project: Another Project')).toBeInTheDocument();

      // Check that project descriptions are rendered (truncated text)
      expect(screen.getByText('This is a test project...')).toBeInTheDocument();

      // Check that project grid is present
      expect(screen.getByRole('grid', { name: '项目列表' })).toBeInTheDocument();
    });

    test('should handle card click events', () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Click on the first project card
      const projectCard = screen.getByLabelText('Project: Test Project 1');
      fireEvent.click(projectCard);

      expect(mockOnCardClick).toHaveBeenCalledWith(1);
    });

    test('should handle edit button clicks', async () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Find and click edit button for first project
      const editButtons = screen.getAllByLabelText(/编辑项目/i);
      fireEvent.click(editButtons[0]);

      expect(mockOnEdit).toHaveBeenCalledWith(1);
    });

    test('should handle delete button clicks', async () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Find and click delete button for first project
      const deleteButtons = screen.getAllByLabelText(/删除项目/i);
      fireEvent.click(deleteButtons[0]);

      expect(mockOnDelete).toHaveBeenCalledWith(1);
    });
  });

  describe('Data Validation and Error Handling', () => {
    test('should handle mixed valid and invalid project data', () => {
      render(
        <ProjectOverview
          projects={mockInvalidProjects as any}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Should show validation warnings
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Some projects have data issues')).toBeInTheDocument();

      // Should still render the valid project (check by aria-label since text is truncated)
      expect(screen.getByLabelText('Project: Valid Project')).toBeInTheDocument();

      // Should show warning about invalid projects
      expect(screen.getByText(/project\(s\) could not be loaded properly/)).toBeInTheDocument();
    });

    test('should provide fallback values for missing project fields', () => {
      const projectWithMissingFields = {
        project_id: 1,
        project_name: '',
        description: null,
        project_status: 'unknown',
        updated_at: '',
        db_type: 'unknown'
      };

      render(
        <ProjectOverview
          projects={[projectWithMissingFields] as any}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Should render with fallback values (check by aria-label since text is truncated)
      expect(screen.getByLabelText('Project: Project 1')).toBeInTheDocument(); // Fallback name
      expect(screen.getByText('Inactive')).toBeInTheDocument(); // Fallback status
    });

    test('should handle completely invalid project data gracefully', () => {
      const invalidData = [
        null,
        undefined,
        'not-an-object',
        123,
        [],
        { invalid: 'data' }
      ];

      render(
        <ProjectOverview
          projects={invalidData as any}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Should show empty state with error message
      expect(screen.getByText('No projects found')).toBeInTheDocument();
      expect(screen.getByText('Some projects could not be loaded due to invalid data.')).toBeInTheDocument();
    });
  });

  describe('Handler Error Handling', () => {
    test('should handle missing onCardClick handler gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });

      render(
        <ProjectOverview
          projects={mockValidProjects}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');
      fireEvent.click(projectCard);

      expect(consoleSpy).toHaveBeenCalledWith('No onCardClick handler provided');
      consoleSpy.mockRestore();
    });

    test('should handle errors in event handlers', () => {
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
      const faultyHandler = vi.fn(() => {
        throw new Error('Handler error');
      });

      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={faultyHandler}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');
      fireEvent.click(projectCard);

      expect(errorSpy).toHaveBeenCalledWith('Error handling card click:', expect.any(Error));
      errorSpy.mockRestore();
    });
  });

  describe('Responsive Behavior', () => {
    test('should maintain accessibility at minimum viewport width', () => {
      // Mock viewport width
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });

      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Check that content is still accessible (check by aria-label since text is truncated)
      expect(screen.getByRole('grid')).toBeInTheDocument();
      expect(screen.getByLabelText('Project: Test Project 1')).toBeInTheDocument();

      // Check that interactive elements are still clickable
      const projectCard = screen.getByLabelText('Project: Test Project 1');
      expect(projectCard).toBeInTheDocument();
    });
  });

  describe('Tooltip Integration', () => {
    test('should show tooltip on hover with complete project information', async () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');

      // Hover over the card
      fireEvent.mouseEnter(projectCard);

      // Wait for tooltip to appear (500ms delay)
      await waitFor(() => {
        expect(screen.getByTestId('hover-tooltip')).toBeInTheDocument();
      }, { timeout: 1000 });

      // Check tooltip content
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('This is a test project description')).toBeInTheDocument();
      expect(screen.getByText('mysql')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
    });

    test('should hide tooltip on mouse leave', async () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');

      // Hover and then leave
      fireEvent.mouseEnter(projectCard);
      fireEvent.mouseLeave(projectCard);

      // Tooltip should not appear
      await waitFor(() => {
        expect(screen.queryByTestId('hover-tooltip')).not.toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Modal Integration', () => {
    test('should open modal when "查看完整详情" is clicked', async () => {
      const projectWithLongDescription = {
        ...mockValidProjects[0],
        description: 'This is a very long description that will definitely need truncation because it exceeds the available space in the project card and should trigger the "查看完整详情" link to appear'
      };

      render(
        <ProjectOverview
          projects={[projectWithLongDescription]}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Find and click the "查看完整详情" link
      const viewDetailsLink = screen.getByText('查看完整详情');
      fireEvent.click(viewDetailsLink);

      // Check that modal opens
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      });
    });

    test('should close modal when ESC is pressed', async () => {
      const projectWithLongDescription = {
        ...mockValidProjects[0],
        description: 'This is a very long description that will definitely need truncation because it exceeds the available space in the project card and should trigger the "查看完整详情" link to appear'
      };

      render(
        <ProjectOverview
          projects={[projectWithLongDescription]}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Open modal
      const viewDetailsLink = screen.getByText('查看完整详情');
      fireEvent.click(viewDetailsLink);

      // Wait for modal to open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Press ESC to close
      fireEvent.keyDown(document, { key: 'Escape' });

      // Modal should close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    test('should close modal when backdrop is clicked', async () => {
      const projectWithLongDescription = {
        ...mockValidProjects[0],
        description: 'This is a very long description that will definitely need truncation because it exceeds the available space in the project card and should trigger the "查看完整详情" link to appear'
      };

      render(
        <ProjectOverview
          projects={[projectWithLongDescription]}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Open modal
      const viewDetailsLink = screen.getByText('查看完整详情');
      fireEvent.click(viewDetailsLink);

      // Wait for modal to open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Click backdrop to close
      const modal = screen.getByRole('dialog');
      fireEvent.click(modal);

      // Modal should close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Complete Feature Integration', () => {
    test('should integrate all components with full user workflow', async () => {
      const projectWithVariousFeatures = {
        project_id: 1,
        project_name: 'Integration Test Project',
        description: 'This is a comprehensive integration test description that will test truncation, tooltips, modals, and all interactive features working together seamlessly',
        project_status: 'active' as const,
        updated_at: new Date().toISOString(),
        db_type: 'postgresql' as const
      };

      render(
        <ProjectOverview
          projects={[projectWithVariousFeatures]}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // 1. Verify card renders with all components
      const projectCard = screen.getByLabelText('Project: Integration Test Project');
      expect(projectCard).toBeInTheDocument();

      // 2. Test hover tooltip functionality
      fireEvent.mouseEnter(projectCard);
      await waitFor(() => {
        expect(screen.getByTestId('hover-tooltip')).toBeInTheDocument();
      }, { timeout: 1000 });

      // Verify tooltip content
      expect(screen.getByText('Integration Test Project')).toBeInTheDocument();
      expect(screen.getByText('postgresql')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();

      // 3. Test tooltip disappears on mouse leave
      fireEvent.mouseLeave(projectCard);
      await waitFor(() => {
        expect(screen.queryByTestId('hover-tooltip')).not.toBeInTheDocument();
      });

      // 4. Test modal opening from truncated description
      const viewDetailsLink = screen.getByText('查看完整详情');
      fireEvent.click(viewDetailsLink);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Verify modal content
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveTextContent('Integration Test Project');
      expect(modal).toHaveTextContent('This is a comprehensive integration test description');
      expect(modal).toHaveTextContent('PostgreSQL');
      expect(modal).toHaveTextContent('Active');

      // 5. Test modal closing
      const closeButton = screen.getByLabelText('Close modal');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      // 6. Test card click navigation
      fireEvent.click(projectCard);
      expect(mockOnCardClick).toHaveBeenCalledWith(1);

      // 7. Test action buttons
      const editButton = screen.getByLabelText('编辑项目 1');
      const deleteButton = screen.getByLabelText('删除项目 1');

      fireEvent.click(editButton);
      expect(mockOnEdit).toHaveBeenCalledWith(1);

      fireEvent.click(deleteButton);
      expect(mockOnDelete).toHaveBeenCalledWith(1);
    });

    test('should handle multiple projects with different states', () => {
      const mixedProjects = [
        {
          project_id: 1,
          project_name: 'Short',
          description: 'Short desc',
          project_status: 'active' as const,
          updated_at: '2023-12-01T10:00:00Z',
          db_type: 'mysql' as const
        },
        {
          project_id: 2,
          project_name: 'Very Long Project Name That Should Be Truncated',
          description: 'This is a very long description that should definitely be truncated and show the view details link because it exceeds the available space in the project card display area',
          project_status: 'inactive' as const,
          updated_at: new Date().toISOString(), // Today's date
          db_type: 'sqlite' as const
        }
      ];

      render(
        <ProjectOverview
          projects={mixedProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Verify both cards render
      expect(screen.getByLabelText('Project: Short')).toBeInTheDocument();
      expect(screen.getByLabelText('Project: Very Long Project Name That Should Be Truncated')).toBeInTheDocument();

      // Verify different database icons
      expect(screen.getByAltText('MySQL Database')).toBeInTheDocument();
      expect(screen.getByAltText('SQLite Database')).toBeInTheDocument();

      // Verify different status badges
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();

      // Verify date formatting (today vs full date)
      expect(screen.getByText(/今天/)).toBeInTheDocument(); // Today format
      expect(screen.getByText(/2023-12-01/)).toBeInTheDocument(); // Full date format

      // Verify truncation behavior
      expect(screen.getByText('查看完整详情')).toBeInTheDocument(); // Only for long description
    });
  });

  describe('Error Recovery and Resilience', () => {
    test('should recover from component errors gracefully', () => {
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

      // Project with data that might cause component errors
      const problematicProject = {
        project_id: 1,
        project_name: 'Test Project',
        description: 'Test description',
        project_status: 'active' as const,
        updated_at: 'invalid-date-format',
        db_type: 'mysql' as const
      };

      render(
        <ProjectOverview
          projects={[problematicProject]}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Should still render the project card with fallback values
      expect(screen.getByLabelText('Project: Test Project')).toBeInTheDocument();

      errorSpy.mockRestore();
    });

    test('should handle network-like errors in handlers', () => {
      const networkErrorHandler = vi.fn(() => {
        throw new Error('Network error');
      });

      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={networkErrorHandler}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');

      // Should not crash when handler throws
      expect(() => {
        fireEvent.click(projectCard);
      }).not.toThrow();

      expect(errorSpy).toHaveBeenCalledWith('Error handling card click:', expect.any(Error));

      errorSpy.mockRestore();
    });

    test('should maintain functionality when CSS fails to load', () => {
      // Simulate CSS loading failure by removing CSS classes
      const originalQuerySelector = document.querySelector;
      document.querySelector = vi.fn((selector) => {
        if (selector.includes('project-card')) {
          return null; // Simulate missing CSS
        }
        return originalQuerySelector.call(document, selector);
      });

      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Should still render content even without CSS
      expect(screen.getByLabelText('Project: Test Project 1')).toBeInTheDocument();

      // Restore original function
      document.querySelector = originalQuerySelector;
    });
  });

  describe('Performance and Memory Management', () => {
    test('should handle large numbers of projects efficiently', () => {
      const manyProjects = Array.from({ length: 100 }, (_, index) => ({
        project_id: index + 1,
        project_name: `Project ${index + 1}`,
        description: `Description for project ${index + 1}`,
        project_status: (index % 3 === 0 ? 'initializing' : index % 3 === 1 ? 'active' : 'inactive') as 'initializing' | 'active' | 'inactive',
        updated_at: new Date(2023, 0, index + 1).toISOString(),
        db_type: (['mysql', 'postgresql', 'sqlite'] as const)[index % 3]
      }));

      const startTime = performance.now();

      render(
        <ProjectOverview
          projects={manyProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (less than 1 second)
      expect(renderTime).toBeLessThan(1000);

      // Should render all projects
      expect(screen.getAllByLabelText(/Project:/).length).toBe(100);
    });

    test('should clean up event listeners and timers', () => {
      vi.useFakeTimers();

      const { unmount } = render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const projectCard = screen.getByLabelText('Project: Test Project 1');

      // Trigger hover to start tooltip timer
      fireEvent.mouseEnter(projectCard);

      // Unmount component
      unmount();

      // Should not cause memory leaks or errors
      expect(() => {
        // Simulate time passing
        vi.advanceTimersByTime(1000);
      }).not.toThrow();

      vi.useRealTimers();
    });
  });

  describe('Accessibility Integration', () => {
    test('should maintain accessibility across all interactive elements', () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Check main container accessibility
      const grid = screen.getByRole('grid');
      expect(grid).toHaveAttribute('aria-label', '项目列表');

      // Check card accessibility
      const projectCard = screen.getByLabelText('Project: Test Project 1');
      expect(projectCard).toHaveAttribute('role', 'button');
      expect(projectCard).toHaveAttribute('tabIndex', '0');

      // Check action button accessibility
      const editButton = screen.getByLabelText('编辑项目 1');
      const deleteButton = screen.getByLabelText('删除项目 1');

      expect(editButton).toHaveAttribute('title', '编辑项目');
      expect(deleteButton).toHaveAttribute('title', '删除项目');

      // Check keyboard navigation
      projectCard.focus();
      expect(document.activeElement).toBe(projectCard);

      // Test keyboard interaction
      fireEvent.keyDown(projectCard, { key: 'Enter' });
      expect(mockOnCardClick).toHaveBeenCalledWith(1);
    });

    test('should provide proper ARIA labels for screen readers', () => {
      render(
        <ProjectOverview
          projects={mockValidProjects}
          onCardClick={mockOnCardClick}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // Check status badge accessibility
      const statusBadge = screen.getByLabelText('项目状态: Active');
      expect(statusBadge).toBeInTheDocument();

      // Check database icon accessibility
      const databaseIcon = screen.getByAltText('MySQL Database');
      expect(databaseIcon).toBeInTheDocument();
    });
  });
});