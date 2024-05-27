import pytest
from faunanet.utils import update_dict_leafs_recursive, read_yaml
from pathlib import Path
import yaml


def test_update_dict_leafs_recursive():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    update = {"b": {"c": 4}}
    update_dict_leafs_recursive(base, update)
    assert base == {"a": 1, "b": {"c": 4, "d": 3}}

    base = {"a": 1, "b": {"c": 2, "d": 3}}
    update = {"b": {"e": 4}}
    update_dict_leafs_recursive(base, update)
    assert base == {"a": 1, "b": {"c": 2, "d": 3}}


def test_read_yaml(tmpdir):
    # Create a temporary yaml file
    p = Path(tmpdir) / "test.yaml"
    data = {"a": 1, "b": 2}
    with p.open("w") as f:
        yaml.safe_dump(data, f)

    # Test read_yaml function
    result = read_yaml(str(p))
    assert result == data

    # Test FileNotFoundError
    with pytest.raises(FileNotFoundError):
        read_yaml("/non/existent/path.yaml")
