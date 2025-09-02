"""
Main test suite runner and CLI logic.
"""
import sys
import argparse
import unittest
from tests.test_client import ClientUnitTests
from tests.test_server import ServerUnitTests
from tests.test_integration import IntegrationTests
from tests.test_hash import HashVerificationTests
from tests.test_stress import StressTests
from tests.test_mock import MockTests
from tests.test_legacy import LegacyIntegrationTest

class TestSuiteRunner:
    """
    Comprehensive test suite runner for the text analysis system.
    
    Manages and executes different categories of tests including unit tests,
    integration tests, stress tests, and hash verification tests. Provides
    detailed reporting and summary statistics.
    
    Attributes:
        test_classes (list): List of test case classes to execute
        results (dict): Dictionary storing test results for each class
    """
    def __init__(self):
        self.test_classes = [
            ClientUnitTests,
            ServerUnitTests,
            IntegrationTests,
            HashVerificationTests,
            StressTests,
            MockTests
        ]
        self.results = {}

    def run_all_tests(self, verbose=True):
        """
        Execute all configured test classes and generate comprehensive reports.
        
        Args:
            verbose (bool): Enable detailed test output and progress information
            
        Returns:
            bool: True if all tests passed, False if any failures or errors occurred
        """
        print("=" * 80)
        print("COMPREHENSIVE TEST SUITE FOR TEXT ANALYSIS SYSTEM")
        print("=" * 80)
        total_tests = 0
        total_failures = 0
        total_errors = 0
        for test_class in self.test_classes:
            print(f"\n{'-' * 60}")
            print(f"Running {test_class.__name__}")
            print(f"{'-' * 60}")
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
            result = runner.run(suite)
            self.results[test_class.__name__] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'success': result.wasSuccessful()
            }
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            if result.wasSuccessful():
                print(f"PASS {test_class.__name__}: ALL TESTS PASSED")
            else:
                print(f"FAIL {test_class.__name__}: {len(result.failures)} failures, {len(result.errors)} errors")
        self._print_summary(total_tests, total_failures, total_errors)
        return total_failures == 0 and total_errors == 0

    def _print_summary(self, total_tests, total_failures, total_errors):
        """
        Print a comprehensive summary of test results.
        
        Args:
            total_tests (int): Total number of tests executed
            total_failures (int): Number of test failures
            total_errors (int): Number of test errors
        """
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        for class_name, results in self.results.items():
            status = "PASS" if results['success'] else "FAIL"
            print(f"{class_name:30} | {results['tests_run']:3} tests | {status}")
        print("-" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Failures: {total_failures}")
        print(f"Errors: {total_errors}")
        if total_failures == 0 and total_errors == 0:
            print("\nALL TESTS PASSED!")
        else:
            print(f"\n{total_failures + total_errors} tests failed")
        print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Text Analysis System Test Suite')
    parser.add_argument('--mode', choices=['all', 'unit', 'integration', 'legacy'], 
                       default='all', help='Test mode to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    args = parser.parse_args()
    if args.mode == 'legacy':
        legacy_test = LegacyIntegrationTest()
        success = legacy_test.run_legacy_test()
        sys.exit(0 if success else 1)
    elif args.mode == 'all':
        runner = TestSuiteRunner()
        success = runner.run_all_tests(verbose=args.verbose)
        if success:
            print("\nRunning legacy integration test...")
            legacy_test = LegacyIntegrationTest()
            legacy_success = legacy_test.run_legacy_test()
            success = success and legacy_success
        sys.exit(0 if success else 1)
    elif args.mode == 'unit':
        unit_classes = [ClientUnitTests, ServerUnitTests, HashVerificationTests, 
                       StressTests, MockTests]
        runner = TestSuiteRunner()
        runner.test_classes = unit_classes
        success = runner.run_all_tests(verbose=args.verbose)
        sys.exit(0 if success else 1)
    elif args.mode == 'integration':
        integration_classes = [IntegrationTests]
        runner = TestSuiteRunner()
        runner.test_classes = integration_classes
        success = runner.run_all_tests(verbose=args.verbose)
        sys.exit(0 if success else 1)
