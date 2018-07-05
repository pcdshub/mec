from hutch_python.utils import safe_load


with safe_load('example'):
    1/0
