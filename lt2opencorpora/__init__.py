__version__ = '1.0.0'

try:
    from .convert import Dictionary
except ImportError:
    # To make setup.py work
    pass
