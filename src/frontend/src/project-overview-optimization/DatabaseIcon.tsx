/**
 * DatabaseIcon Component
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
 * 
 * Displays database type icons for project cards with proper sizing and fallback handling.
 */

import React from 'react';
import { DatabaseIconProps } from '../types/project-overview';
import { DATABASE_ICON_SIZE, CSS_CLASSES } from '../constants/project-overview';

const DatabaseIcon: React.FC<DatabaseIconProps> = ({
  dbType,
  size = DATABASE_ICON_SIZE,
  className = ''
}) => {
  // Icon path mapping based on database type (Requirements 4.2, 4.3, 4.4)
  const getIconPath = (type: string): string => {
    switch (type) {
      case 'mysql':
        return '/mysql-logo.svg';
      case 'postgresql':
        return '/postgresql-logo.svg';
      case 'sqlite':
        return '/sqlite-logo.svg';
      default:
        // Fallback for unknown types (Requirement 4.6)
        return '/database-logo.svg';
    }
  };

  // Get alt text for accessibility
  const getAltText = (type: string): string => {
    switch (type) {
      case 'mysql':
        return 'MySQL Database';
      case 'postgresql':
        return 'PostgreSQL Database';
      case 'sqlite':
        return 'SQLite Database';
      default:
        return 'Database';
    }
  };

  const iconPath = getIconPath(dbType);
  const altText = getAltText(dbType);

  return (
    <img
      src={iconPath}
      alt={altText}
      className={`${CSS_CLASSES.databaseIcon} ${className}`.trim()}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        // Requirement 4.5: 20x20 pixel sizing with proper margins
        marginRight: '8px',
        flexShrink: 0,
        objectFit: 'contain'
      }}
      // Handle image loading errors by falling back to generic icon
      onError={(e) => {
        const target = e.target as HTMLImageElement;
        if (target.src !== '/database-logo.svg') {
          target.src = '/database-logo.svg';
          target.alt = 'Database';
        }
      }}
    />
  );
};

export default DatabaseIcon;