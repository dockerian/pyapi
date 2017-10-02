"""
Provides code conformance testing.

See: http://blog.jameskyle.org/2014/05/pep8-pylint-tests-with-nose-xunit/
"""
import os
import pep8
import re

from nose.tools import assert_true  # pylint: disable=E0611

PROJ_ROOT = "catalog-api/globalapi"


def fail(msg):
    """
    Fails with message.
    """
    assert_true(False, msg)


class CustomReport(pep8.StandardReport):
    """
    Collect report into an array of results.
    """
    results = []

    def get_file_results(self):
        if self._deferred_print:
            self._deferred_print.sort()
            for line_number, offset, code, text, _ in self._deferred_print:
                self.results.append({
                    'path': self.filename,
                    'row': self.line_offset + line_number,
                    'col': offset + 1,
                    'code': code,
                    'text': text,
                })
        return self.file_errors


def test_pep8_conformance():
    """
    Test for pep8 conformance
    """
    pattern = re.compile(r'.*({0}.*\.py)'.format(PROJ_ROOT))
    pep8style = pep8.StyleGuide(max_line_length=100, reporter=CustomReport)
    base = os.path.dirname(os.path.abspath(__file__))
    dirname = os.path.abspath(os.path.join(base, '..'))
    sources = [
        os.path.join(root, pyfile) for root, _, files in os.walk(dirname)
        for pyfile in files
        if pyfile.endswith('.py')]
    report = pep8style.init_report()
    pep8style.check_files(sources)

    for error in report.results:
        msg = "{path}: {code} {row}, {col} - {text}"
        match = pattern.match(error['path'])
        if match:
            rel_path = match.group(1)
        else:
            rel_path = error['path']

        yield fail, msg.format(
            path=rel_path,
            code=error['code'],
            row=error['row'],
            col=error['col'],
            text=error['text']
        )
