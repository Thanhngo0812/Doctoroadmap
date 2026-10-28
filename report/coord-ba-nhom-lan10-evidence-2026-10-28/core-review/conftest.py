"""Offline reviewer probes: accept the standard runner flag, never create a PG fixture."""
def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true')
