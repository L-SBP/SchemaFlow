/**
 * Database icon assets and import paths
 * Requirements: 4.2, 4.3, 4.4, 4.6
 */

// Database icon asset paths
export const DATABASE_ICON_PATHS = {
  mysql: '/mysql-logo.svg',
  postgresql: '/postgresql-logo.svg',
  sqlite: '/sqlite-logo.svg',
  generic: '/database-logo.svg',
} as const;

// Database type validation
export type DatabaseType = 'mysql' | 'postgresql' | 'sqlite';

// Database icon configuration
export interface DatabaseIconConfig {
  path: string;
  alt: string;
  title: string;
}

// Database icon configurations
export const DATABASE_ICON_CONFIGS: Record<DatabaseType | 'generic', DatabaseIconConfig> = {
  mysql: {
    path: DATABASE_ICON_PATHS.mysql,
    alt: 'MySQL Database',
    title: 'MySQL Database',
  },
  postgresql: {
    path: DATABASE_ICON_PATHS.postgresql,
    alt: 'PostgreSQL Database',
    title: 'PostgreSQL Database',
  },
  sqlite: {
    path: DATABASE_ICON_PATHS.sqlite,
    alt: 'SQLite Database',
    title: 'SQLite Database',
  },
  generic: {
    path: DATABASE_ICON_PATHS.generic,
    alt: 'Database',
    title: 'Database',
  },
};

/**
 * Get database icon configuration for a given database type
 * Falls back to generic icon for unknown types (Requirement 4.6)
 */
export function getDatabaseIconConfig(dbType: string | null | undefined): DatabaseIconConfig {
  if (!dbType || !isDatabaseType(dbType)) {
    return DATABASE_ICON_CONFIGS.generic;
  }
  return DATABASE_ICON_CONFIGS[dbType];
}

/**
 * Type guard to check if a string is a valid database type
 */
export function isDatabaseType(value: string): value is DatabaseType {
  return ['mysql', 'postgresql', 'sqlite'].includes(value);
}

/**
 * Get all available database types
 */
export function getAvailableDatabaseTypes(): DatabaseType[] {
  return ['mysql', 'postgresql', 'sqlite'];
}