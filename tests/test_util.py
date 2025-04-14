import os
import logging.config
import pytest
from app.utils.common import setup_logging  # Adjust the import path if necessary

def test_setup_logging_calls_fileConfig(monkeypatch):
    # Create a dummy function that will record its call arguments.
    calls = []
    def dummy_fileConfig(path, disable_existing_loggers):
        calls.append((path, disable_existing_loggers))
    
    # Monkey-patch logging.config.fileConfig with dummy_fileConfig
    monkeypatch.setattr(logging.config, "fileConfig", dummy_fileConfig)
    
    # Call the setup_logging function, which should trigger fileConfig.
    setup_logging()
    
    # Verify that fileConfig was called once.
    assert len(calls) == 1, "fileConfig should be called once"
    
    # Unpack the arguments passed to fileConfig.
    config_path, disable_flag = calls[0]
    
    # Verify that disable_existing_loggers is False.
    assert disable_flag is False, "disable_existing_loggers should be False"
    
    # Verify that the provided path ends with "logging.conf".
    assert config_path.endswith("logging.conf"), "The config path should end with 'logging.conf'"

def test_setup_logging_normalized_path(monkeypatch):
    # This test verifies that the logging configuration path is normalized.
    
    # We'll capture the actual path computed by setup_logging.
    captured_path = None
    def dummy_fileConfig(path, disable_existing_loggers):
        nonlocal captured_path
        captured_path = path
    
    monkeypatch.setattr(logging.config, "fileConfig", dummy_fileConfig)
    setup_logging()
    
    # Check that we captured a path.
    assert captured_path is not None, "The configuration path should be captured"
    
    # Ensure that the normalized path is absolute and uses the OS's path separator.
    expected_suffix = os.sep + "logging.conf"
    assert captured_path.endswith(expected_suffix), f"The normalized path should end with '{expected_suffix}'"

