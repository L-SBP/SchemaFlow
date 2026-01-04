#!/usr/bin/env node

/**
 * TypeScript Compilation Check Script
 * This script verifies that all TypeScript files compile without errors
 * and provides detailed reporting of any issues found.
 */

import { execSync } from 'child_process';
import { existsSync } from 'fs';
import path from 'path';

interface CompilationResult {
  success: boolean;
  errors: string[];
  warnings: string[];
  totalFiles: number;
  errorCount: number;
}

class TypeScriptCompilationChecker {
  private projectRoot: string;
  private tsconfigPath: string;

  constructor() {
    this.projectRoot = process.cwd();
    this.tsconfigPath = path.join(this.projectRoot, 'tsconfig.json');
  }

  /**
   * Check if TypeScript configuration exists
   */
  private checkTsConfig(): boolean {
    if (!existsSync(this.tsconfigPath)) {
      console.error('❌ tsconfig.json not found in project root');
      return false;
    }
    console.log('✅ Found tsconfig.json');
    return true;
  }

  /**
   * Run TypeScript compiler and capture output
   */
  private runTypeScriptCompiler(): CompilationResult {
    try {
      console.log('🔍 Running TypeScript compiler...');

      // Run tsc with noEmit flag to only check types
      const output = execSync('npx tsc --noEmit --pretty false', {
        encoding: 'utf8',
        cwd: this.projectRoot
      });

      return {
        success: true,
        errors: [],
        warnings: [],
        totalFiles: 0,
        errorCount: 0
      };

    } catch (error: any) {
      const output = error.stdout || error.message || '';
      const lines = output.split('\n').filter((line: string) => line.trim());

      const errors: string[] = [];
      const warnings: string[] = [];
      let errorCount = 0;

      lines.forEach((line: string) => {
        if (line.includes(' error TS')) {
          errors.push(line);
          errorCount++;
        } else if (line.includes(' warning TS')) {
          warnings.push(line);
        }
      });

      return {
        success: false,
        errors,
        warnings,
        totalFiles: 0,
        errorCount
      };
    }
  }

  /**
   * Categorize errors by type
   */
  private categorizeErrors(errors: string[]): Record<string, string[]> {
    const categories: Record<string, string[]> = {
      'Unused Variables': [],
      'Type Errors': [],
      'Import Errors': [],
      'Property Errors': [],
      'Mock Errors': [],
      'Other': []
    };

    errors.forEach(error => {
      if (error.includes('is declared but its value is never read')) {
        categories['Unused Variables'].push(error);
      } else if (error.includes('Type ') || error.includes('not assignable')) {
        categories['Type Errors'].push(error);
      } else if (error.includes('import') || error.includes('module')) {
        categories['Import Errors'].push(error);
      } else if (error.includes('Property') || error.includes('does not exist')) {
        categories['Property Errors'].push(error);
      } else if (error.includes('mock') || error.includes('Mock')) {
        categories['Mock Errors'].push(error);
      } else {
        categories['Other'].push(error);
      }
    });

    return categories;
  }

  /**
   * Generate compilation report
   */
  private generateReport(result: CompilationResult): void {
    console.log('\n📊 TypeScript Compilation Report');
    console.log('================================');

    if (result.success) {
      console.log('✅ All TypeScript files compiled successfully!');
      console.log('🎉 No type errors found.');
      return;
    }

    console.log(`❌ Compilation failed with ${result.errorCount} errors`);

    if (result.warnings.length > 0) {
      console.log(`⚠️  ${result.warnings.length} warnings found`);
    }

    // Categorize and display errors
    const categorizedErrors = this.categorizeErrors(result.errors);

    Object.entries(categorizedErrors).forEach(([category, errors]) => {
      if (errors.length > 0) {
        console.log(`\n📂 ${category} (${errors.length}):`);
        errors.slice(0, 5).forEach(error => {
          console.log(`   ${error}`);
        });
        if (errors.length > 5) {
          console.log(`   ... and ${errors.length - 5} more`);
        }
      }
    });

    // Provide recommendations
    this.provideRecommendations(categorizedErrors);
  }

  /**
   * Provide recommendations based on error types
   */
  private provideRecommendations(categorizedErrors: Record<string, string[]>): void {
    console.log('\n💡 Recommendations:');

    if (categorizedErrors['Unused Variables'].length > 0) {
      console.log('• Remove unused variables or prefix with underscore (_variable)');
    }

    if (categorizedErrors['Type Errors'].length > 0) {
      console.log('• Review type definitions and ensure proper type annotations');
    }

    if (categorizedErrors['Property Errors'].length > 0) {
      console.log('• Check object property names and interface definitions');
    }

    if (categorizedErrors['Mock Errors'].length > 0) {
      console.log('• Update test mocks to match current API signatures');
    }

    console.log('• Consider using TypeScript strict mode for better type safety');
    console.log('• Run "npx tsc --noEmit" for detailed error information');
  }

  /**
   * Main execution method
   */
  public async run(): Promise<boolean> {
    console.log('🚀 Starting TypeScript Compilation Check...\n');

    // Check if tsconfig exists
    if (!this.checkTsConfig()) {
      return false;
    }

    // Run compilation check
    const result = this.runTypeScriptCompiler();

    // Generate report
    this.generateReport(result);

    return result.success;
  }
}

// Execute if run directly
if (require.main === module) {
  const checker = new TypeScriptCompilationChecker();
  checker.run().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('❌ Compilation check failed:', error);
    process.exit(1);
  });
}

export default TypeScriptCompilationChecker;