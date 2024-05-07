import pytest
from repl import SparrowCmd, process_line
from unittest.mock import Mock


def test_do_start(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("")
    mock_watcher_instance.start.assert_called_once()


def test_do_stop(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_stop("")
    mock_watcher_instance.stop.assert_called_once()


def test_do_pause(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_pause("")
    mock_watcher_instance.pause.assert_called_once()


def test_do_continue(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = True
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_continue("")
    mock_watcher_instance.go_on.assert_called_once()


def test_do_restart(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_restart("")
    mock_watcher_instance.restart.assert_called_once()


def test_do_exit(mocker):
    sparrow_cmd = SparrowCmd()
    assert sparrow_cmd.do_exit("") == True


def test_clean_up(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.clean_up("")
    mock_watcher_instance.clean_up.assert_called_once()


def test_change_analyzer(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.change_analyzer("--cfg=test")
    mock_watcher_instance.change_analyzer.assert_called_once()


def test_process_line():
    assert process_line("--cfg=test") == ["test"]
    assert process_line("--cfg=test --cfg2=test2") == ["test", "test2"]
    assert process_line("") == []
    assert process_line("--cfg") == None
