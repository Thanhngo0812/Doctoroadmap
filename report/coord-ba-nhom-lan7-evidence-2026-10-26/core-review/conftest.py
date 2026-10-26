def pytest_addoption(parser):
    parser.addoption('--w16-review-mutant', default='none')

import socket
import pytest

@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    connect = socket.socket.connect
    def forbid_external(self, address):
        # Windows asyncio creates a loopback socketpair before ASGI HTTP runs.
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1') and address[1] not in (5432, 5433):
            return connect(self, address)
        raise AssertionError('R7 offline review forbids external/DB connections')
    monkeypatch.setattr(socket.socket, 'connect', forbid_external)
