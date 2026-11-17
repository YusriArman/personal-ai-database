from pathlib import Path

import pytest

from app.index.db import connect
from app.index.indexer import rescan
from app.providers.fake import FakeProvider

DEMO_VAULT = Path(__file__).resolve().parents[2] / "demo_vault"


@pytest.fixture
def provider():
    return FakeProvider()


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def vault(tmp_path):
    """A tiny vault that tests can freely edit."""
    root = tmp_path / "vault"
    root.mkdir()
    (root / "Alpha.md").write_text(
        "---\ntags: [space]\n---\n# Alpha\n\nRockets burn kerosene and oxygen. See [[Beta]] "
        "and [[Missing Note]].\n\n- [ ] Order the nozzle\n- [x] Weld the tank\n"
    )
    (root / "Beta.md").write_text(
        "# Beta\n\nOrbital mechanics: an orbit is a constant fall around a planet.\n\n"
        "I need to email Dana about the launch window.\n"
    )
    (root / "Gamma.md").write_text(
        "# Gamma\n\nSourdough bread needs flour, water and patience. Rockets are unrelated.\n"
    )
    return root


@pytest.fixture
def indexed(conn, vault, provider):
    rescan(conn, vault, provider)
    return conn


@pytest.fixture
def demo(conn, provider):
    rescan(conn, DEMO_VAULT, provider)
    return conn
