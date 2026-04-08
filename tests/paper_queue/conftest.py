import pytest
from storage import QueueDB


@pytest.fixture
def queue_db(tmp_path):
    """Create a fresh QueueDB backed by a temporary SQLite file."""
    db_path = str(tmp_path / "test_queue.db")
    db = QueueDB.init_db(db_path)
    yield db
    db.close()
