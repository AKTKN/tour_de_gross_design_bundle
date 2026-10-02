#!/usr/bin/env python3
"""Rerun acceptance tests, recording exact node IDs and setup/call/teardown outcomes."""
import json
from pathlib import Path
import sys
import pytest


class Report:
    def __init__(self):
        self.tests = {}

    def pytest_runtest_logreport(self, report):
        outcome = 'xfail' if hasattr(report, 'wasxfail') else report.outcome
        self.tests.setdefault(report.nodeid, {})[report.when] = outcome


def main():
    output = Path(sys.argv[1])
    reporter = Report()
    code = pytest.main(['-q', '--strict-markers', *sys.argv[2:]], plugins=[reporter])
    output.write_text(json.dumps({'exit_code': int(code), 'tests': reporter.tests}, indent=2) + '\n')
    return int(code)


if __name__ == '__main__':
    sys.exit(main())
