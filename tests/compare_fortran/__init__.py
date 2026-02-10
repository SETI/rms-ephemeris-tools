"""Framework to run FORTRAN and Python tools with the same inputs and compare outputs."""

from tests.compare_fortran.spec import RunSpec
from tests.compare_fortran.runner import run_python, run_fortran
from tests.compare_fortran.diff_utils import compare_tables, compare_postscript, CompareResult

__all__ = [
    "RunSpec",
    "run_python",
    "run_fortran",
    "compare_tables",
    "compare_postscript",
    "CompareResult",
]
