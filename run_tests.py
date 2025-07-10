#!/usr/bin/env python3
"""
Test runner script for EustatsPy.

This script provides convenient ways to run different types of tests
and generate reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"{'='*60}")
    
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for EustatsPy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --fast             # Run fast tests only
  python run_tests.py --coverage         # Run with detailed coverage
  python run_tests.py --parallel         # Run tests in parallel
  python run_tests.py --file test_client # Run specific test file
        """
    )
    
    # Test selection options
    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--fast', action='store_true',
                       help='Run fast tests only (exclude slow tests)')
    parser.add_argument('--slow', action='store_true',
                       help='Run slow tests only')
    
    # Test execution options
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate detailed coverage report')
    parser.add_argument('--no-cov', action='store_true',
                       help='Disable coverage reporting')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML coverage report')
    
    # Test filtering
    parser.add_argument('--file', type=str,
                       help='Run specific test file (without .py extension)')
    parser.add_argument('--test', type=str,
                       help='Run specific test function or class')
    parser.add_argument('--keyword', '-k', type=str,
                       help='Run tests matching keyword expression')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet output')
    parser.add_argument('--failed-first', action='store_true',
                       help='Run failed tests first')
    
    # Debug options
    parser.add_argument('--pdb', action='store_true',
                       help='Drop into debugger on failures')
    parser.add_argument('--lf', action='store_true',
                       help='Run only last failed tests')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['pytest']
    
    # Add test selection markers
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.fast:
        cmd.extend(['-m', 'not slow'])
    elif args.slow:
        cmd.extend(['-m', 'slow'])
    
    # Add specific file or test
    if args.file:
        test_file = f"tests/test_{args.file}.py"
        if not Path(test_file).exists():
            test_file = f"tests/{args.file}.py"
        cmd.append(test_file)
    
    if args.test:
        if args.file:
            cmd.append(f"::{args.test}")
        else:
            cmd.extend(['-k', args.test])
    
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    
    # Coverage options
    if args.no_cov:
        cmd.append('--no-cov')
    elif args.coverage:
        cmd.extend([
            '--cov=eustatspy',
            '--cov-report=term-missing',
            '--cov-report=xml',
        ])
        if args.html:
            cmd.append('--cov-report=html')
    
    # Execution options
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    # Output options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.failed_first:
        cmd.append('--ff')
    
    if args.lf:
        cmd.append('--lf')
    
    # Debug options
    if args.pdb:
        cmd.append('--pdb')
    
    # Run the tests
    success = run_command(cmd, "Running EustatsPy Tests")
    
    if success:
        print("\n✅ All tests passed!")
        
        if args.coverage or args.html:
            print("\n📊 Coverage report generated:")
            if args.html:
                print("   HTML: htmlcov/index.html")
            print("   XML: coverage.xml")
    else:
        print("\n❌ Some tests failed!")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())