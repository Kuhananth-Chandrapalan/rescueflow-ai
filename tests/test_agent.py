import tempfile
from pathlib import Path
import pytest
from automation.agent import apply_files, check_path
from automation.select_task import mark_complete, select


def test_agent_cannot_write_workflows_or_secrets():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for path in ['.github/workflows/evil.yml', '../outside.py', 'src/.secret',
                     'src/../automation/bad.py', 'requirements.txt', 'src/x.sh']:
            with pytest.raises(ValueError):
                check_path(path, root)


def test_agent_writes_only_source_with_tests():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        output = apply_files({'files': [
            {'path': 'src/rescueflow/feature.py', 'content': 'x = 2\n'},
            {'path': 'tests/test_feature.py', 'content': 'def test_x(): assert 2 == 2\n'}]}, root)
        assert output == ['src/rescueflow/feature.py', 'tests/test_feature.py']


def test_agent_rejects_no_test_change():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        with pytest.raises(ValueError):
            apply_files({'files': [{'path': 'src/feature.py', 'content': 'x = 2\n'}]}, root)


def test_agent_rejects_partial_unsafe_batch():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        with pytest.raises(ValueError):
            apply_files({'files': [
                {'path': 'src/feature.py', 'content': 'x = 2\n'},
                {'path': '.github/workflows/bad.yml', 'content': 'malicious'},
                {'path': 'tests/test_feature.py', 'content': 'assert 1'}]}, root)
        assert not (root / 'src/feature.py').exists()


def test_task_completion_moves_selection(tmp_path):
    (tmp_path / 'tasks').mkdir()
    (tmp_path / 'tasks/backlog.json').write_text('[{"id":"first-task"},{"id":"second-task"}]')
    (tmp_path / 'tasks/completed.json').write_text('[]')
    assert select(tmp_path)['id'] == 'first-task'
    mark_complete('first-task', tmp_path)
    assert select(tmp_path)['id'] == 'second-task'
