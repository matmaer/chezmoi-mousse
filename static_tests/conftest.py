import pytest

from static_tests._ast_nodes import NodeDb

NODE_DB = NodeDb()


@pytest.fixture(scope="session", autouse=True)
def node_db() -> NodeDb:
    return NODE_DB
