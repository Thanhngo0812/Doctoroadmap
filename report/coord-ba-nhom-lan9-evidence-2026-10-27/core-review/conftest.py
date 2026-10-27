def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true')
