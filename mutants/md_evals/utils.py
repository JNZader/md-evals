"""Utility functions for md-evals."""

from pathlib import Path
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


def read_file(path: str) -> str:
    args = [path]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_read_file__mutmut_orig, x_read_file__mutmut_mutants, args, kwargs, None)


def x_read_file__mutmut_orig(path: str) -> str:
    """Read file contents."""
    return Path(path).read_text()


def x_read_file__mutmut_1(path: str) -> str:
    """Read file contents."""
    return Path(None).read_text()

x_read_file__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_read_file__mutmut_1': x_read_file__mutmut_1
}
x_read_file__mutmut_orig.__name__ = 'x_read_file'


def ensure_dir(path: str) -> Path:
    args = [path]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_ensure_dir__mutmut_orig, x_ensure_dir__mutmut_mutants, args, kwargs, None)


def x_ensure_dir__mutmut_orig(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def x_ensure_dir__mutmut_1(path: str) -> Path:
    """Ensure directory exists."""
    p = None
    p.mkdir(parents=True, exist_ok=True)
    return p


def x_ensure_dir__mutmut_2(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(None)
    p.mkdir(parents=True, exist_ok=True)
    return p


def x_ensure_dir__mutmut_3(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=None, exist_ok=True)
    return p


def x_ensure_dir__mutmut_4(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=None)
    return p


def x_ensure_dir__mutmut_5(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(exist_ok=True)
    return p


def x_ensure_dir__mutmut_6(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, )
    return p


def x_ensure_dir__mutmut_7(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=False, exist_ok=True)
    return p


def x_ensure_dir__mutmut_8(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=False)
    return p

x_ensure_dir__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_ensure_dir__mutmut_1': x_ensure_dir__mutmut_1, 
    'x_ensure_dir__mutmut_2': x_ensure_dir__mutmut_2, 
    'x_ensure_dir__mutmut_3': x_ensure_dir__mutmut_3, 
    'x_ensure_dir__mutmut_4': x_ensure_dir__mutmut_4, 
    'x_ensure_dir__mutmut_5': x_ensure_dir__mutmut_5, 
    'x_ensure_dir__mutmut_6': x_ensure_dir__mutmut_6, 
    'x_ensure_dir__mutmut_7': x_ensure_dir__mutmut_7, 
    'x_ensure_dir__mutmut_8': x_ensure_dir__mutmut_8
}
x_ensure_dir__mutmut_orig.__name__ = 'x_ensure_dir'
