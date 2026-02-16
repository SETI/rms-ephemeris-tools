"""Framework to run FORTRAN and Python tools with the same inputs and compare outputs."""

from tests.compare_fortran.diff_utils import CompareResult, compare_postscript, compare_tables
from tests.compare_fortran.runner import run_fortran, run_python
from tests.compare_fortran.spec import RunSpec

__all__ = [
    'CompareResult',
    'RunSpec',
    'compare_postscript',
    'compare_tables',
    'run_fortran',
    'run_python',
]
