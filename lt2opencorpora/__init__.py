__version__ = '2.0.1'

try:
    from .convert import Dictionary
except ImportError:
    # To make setup.py work
    pass
