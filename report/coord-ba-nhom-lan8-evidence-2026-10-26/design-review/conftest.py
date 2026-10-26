# Isolated design-only review; no PostgreSQL test is collected here.
def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true', help='Accepted for the project runner; this isolated suite has no database tests.')
