import socket
import shutil
import subprocess
import time

import pytest
from algokit_utils import AlgorandClient


ALGOD_PORT = 4001
INDEXER_PORT = 8980
LOCALNET_START_CMD = ["algokit", "localnet", "start"]
LOCALNET_WAIT_SECONDS = 60


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("localhost", port), timeout=1):
            return True
    except OSError:
        return False


def _localnet_ready() -> bool:
    if not (_port_open(ALGOD_PORT) and _port_open(INDEXER_PORT)):
        return False

    try:
        client = AlgorandClient.default_localnet()
        client.client.algod.health()
        client.client.indexer.health()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_localnet_running() -> None:
    """Make sure a local Algorand node is reachable before running integration tests."""
    if shutil.which("algokit") is None:
        pytest.skip("Algokit CLI is required to run tests; skipping because it is not installed.")

    if _localnet_ready():
        return

    try:
        subprocess.run(
            LOCALNET_START_CMD, check=True, capture_output=True, text=True
        )
    except FileNotFoundError as exc:
        pytest.fail(f"Algokit CLI is required to run tests: {exc}")
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            f"Failed to start Algokit localnet "
            f"(exit {exc.returncode}): {exc.stdout or exc.stderr}"
        )

    deadline = time.time() + LOCALNET_WAIT_SECONDS
    while time.time() < deadline:
        if _localnet_ready():
            return
        time.sleep(1)

    pytest.fail(
        f"Algokit localnet did not become ready on ports {ALGOD_PORT}/{INDEXER_PORT} "
        f"within {LOCALNET_WAIT_SECONDS} seconds."
    )
