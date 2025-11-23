# Testing Guide for Whisper Worker

This guide explains how to write and run tests for the Whisper worker, with a special focus on using the mock system in the `tests/mock` folder.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Available Fixtures](#available-fixtures)
4. [Mock System](#mock-system)
5. [Using Mocks in Tests](#using-mocks-in-tests)
6. [Test Examples](#test-examples)
7. [Best Practices](#best-practices)
8. [Running Tests](#running-tests)

---

## Overview

The test suite uses a mock system to avoid requiring actual Whisper dependencies, GPU hardware, or real audio processing during tests. This makes tests:
- **Fast**: No actual transcription processing
- **Reliable**: No dependency on external services or hardware
- **Isolated**: Tests don't affect production code

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_worker.py           # Main test suite
├── test_worker_with_mock_*.py  # Examples of different mock approaches
└── mock/                    # Mock system
    ├── __init__.py
    ├── runner.py            # MockWhisperRunner implementation
    └── factory.py           # Test factory helper
```

---

## Available Fixtures

All fixtures are defined in `tests/conftest.py` and are automatically available to all test files.

### `sample_audio`

Creates a temporary dummy audio file for testing. The file is automatically cleaned up after the test.

**Usage:**
```python
def test_something(sample_audio):
    # sample_audio is a path string to a valid audio file
    runner = MockWhisperRunner()
    result = runner.run(sample_audio)
```

**Details:**
- Creates a minimal WAV file (RIFF header + dummy data)
- File is created in a temporary directory
- Automatically cleaned up by pytest
- Always available - no need to create audio files manually

### `mock_runner`

Provides a `MockWhisperRunner` instance ready to use.

**Usage:**
```python
def test_something(mock_runner, sample_audio):
    result = mock_runner.run(sample_audio)
    assert result["engine"] == "mock"
```

### `use_mock_runner`

Automatically patches `worker.tasks.get_runner` to return `MockWhisperRunner` for the entire test.

**Usage:**
```python
from worker.tasks import transcribe

def test_transcribe(use_mock_runner, sample_audio):
    # get_runner is automatically patched
    result = transcribe("job-123", sample_audio, "whisperx")
    assert result["engine"] == "mock"
```

### `use_mock_runner_for_engine`

Context manager for temporary mock usage (less commonly used).

**Usage:**
```python
def test_something(sample_audio):
    with use_mock_runner_for_engine():
        result = transcribe("job-123", sample_audio, "whisperx")
```

---

## Mock System

### Components

#### 1. `MockWhisperRunner` (`tests/mock/runner.py`)

A complete mock implementation of the `BaseRunner` interface that:
- Implements the same interface as real runners (`WhisperXRunner`, `TimestampedRunner`)
- Returns predictable, realistic mock transcription data
- Requires no external dependencies (no Whisper, no GPU)
- Validates audio file existence (but doesn't process it)

**Key Features:**
- Returns `TranscriptionResult` with proper structure
- Includes word-level timestamps
- Generates text based on audio filename
- Respects language parameter
- Validates audio file exists

**Example Output:**
```python
{
    "text": "This is a mock transcription from the file test_audio",
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "This is a mock transcription",
            "words": [
                {"word": "This", "start": 0.0, "end": 0.4},
                {"word": "is", "start": 0.5, "end": 0.7},
                # ... more words
            ]
        },
        # ... more segments
    ],
    "language": "en",
    "engine": "mock"
}
```

#### 2. `get_test_runner()` (`tests/mock/factory.py`)

A test-only factory function that can return either mock or real runners:

```python
from tests.mock.factory import get_test_runner

# Get a mock runner
mock_runner = get_test_runner("whisperx", use_mock=True)

# Get a real runner (for integration tests)
real_runner = get_test_runner("whisperx", use_mock=False)
```

**Parameters:**
- `engine`: Engine name (`"whisperx"`, `"timestamped"`, or `"mock"`)
- `model`: Model size (default: `"base"`)
- `use_mock`: If `True`, always returns `MockWhisperRunner` (default: `False`)

---

## Using Mocks in Tests

There are **three main approaches** to using mocks in your tests, each with different use cases:

### Approach 1: Direct Mock Usage

**When to use:** Testing the mock runner itself or when you need direct control.

**How it works:** Import and instantiate `MockWhisperRunner` directly.

**Example:**
```python
from tests.mock.runner import MockWhisperRunner

def test_transcribe_with_direct_mock(sample_audio):
    """Use mock runner directly without patching."""
    runner = MockWhisperRunner()
    result = runner.run(sample_audio, language="en")
    
    assert result["engine"] == "mock"
    assert "mock transcription" in result["text"].lower()
```

**Pros:**
- Simple and explicit
- No patching required
- Good for testing runner logic directly

**Cons:**
- Doesn't test integration with `transcribe()` function
- Requires manual runner instantiation

---

### Approach 2: Using Test Factory

**When to use:** When you want flexibility to switch between mock and real runners.

**How it works:** Use `get_test_runner()` from `tests/mock/factory.py`.

**Example:**
```python
from tests.mock.factory import get_test_runner
from tests.mock.runner import MockWhisperRunner

def test_with_test_factory(sample_audio):
    """Use test factory helper."""
    runner = get_test_runner("whisperx", use_mock=True)
    assert isinstance(runner, MockWhisperRunner)
    
    result = runner.run(sample_audio)
    assert result["engine"] == "mock"
```

**Pros:**
- Flexible: can switch between mock and real
- Centralized factory logic
- Good for integration tests that might use real runners

**Cons:**
- Still requires manual runner creation
- Doesn't automatically patch `transcribe()`

---

### Approach 3: Using Fixtures (Recommended)

**When to use:** Testing the full `transcribe()` function with automatic mock injection.

**How it works:** Use pytest fixtures from `conftest.py` that automatically patch `get_runner()`.

**Available Fixtures:**

#### `use_mock_runner` (Automatic Patching)

Patches `worker.tasks.get_runner` to return `MockWhisperRunner` for the entire test.

**Example:**
```python
from worker.tasks import transcribe

def test_transcribe_with_fixture(use_mock_runner, sample_audio):
    """Automatic mock injection via fixture."""
    # get_runner is automatically patched
    result = transcribe(
        "job-123",
        sample_audio,
        "whisperx",
        language="en"
    )
    
    assert result["engine"] == "mock"
    assert len(result["segments"]) > 0
```

#### `mock_runner` (Direct Instance)

Provides a `MockWhisperRunner` instance without patching.

**Example:**
```python
def test_with_mock_instance(mock_runner, sample_audio):
    """Use mock runner instance directly."""
    result = mock_runner.run(sample_audio, language="en")
    assert result["engine"] == "mock"
```

#### `use_mock_runner_for_engine` (Context Manager)

Context manager for temporary mock usage.

**Example:**
```python
def test_with_context_manager(sample_audio):
    """Use context manager for temporary mocking."""
    with use_mock_runner_for_engine():
        result = transcribe(
            "job-123",
            sample_audio,
            "whisperx"
        )
        assert result["engine"] == "mock"
```

**Pros:**
- Tests full integration with `transcribe()`
- Automatic cleanup
- Clean, readable test code
- Recommended for most tests

**Cons:**
- Requires understanding of pytest fixtures

---

### Approach 4: Manual Patching

**When to use:** When you need fine-grained control over patching behavior.

**How it works:** Use `unittest.mock.patch` to manually patch `get_runner()`.

**Example:**
```python
from unittest.mock import patch
from tests.mock.runner import MockWhisperRunner
from worker.tasks import transcribe

def test_transcribe_with_patched_runner(sample_audio):
    """Patch get_runner to use mock."""
    with patch("worker.tasks.get_runner") as mock_get:
        mock_get.return_value = MockWhisperRunner()
        
        # Now transcribe will use mock runner
        result = transcribe(
            "job-123",
            sample_audio,
            "whisperx",  # Engine name doesn't matter, mock is returned
            language="en"
        )
        
        assert result["engine"] == "mock"
        mock_get.assert_called_once_with("whisperx", "base")
```

**Pros:**
- Full control over patching
- Can verify function calls
- Good for testing specific behaviors

**Cons:**
- More verbose
- Requires manual cleanup (though `patch` handles it)

---

## Test Examples

### Example 1: Basic Transcription Test

```python
import pytest
from worker.tasks import transcribe

def test_transcribe_success(use_mock_runner, sample_audio):
    """Test successful transcription with mock."""
    result = transcribe(
        "job-123",
        sample_audio,
        "whisperx",
        language="en",
        model="base"
    )
    
    assert result["text"] is not None
    assert len(result["segments"]) > 0
    assert result["language"] == "en"
    assert result["engine"] == "mock"
```

### Example 2: Testing Runner Directly

```python
from tests.mock.runner import MockWhisperRunner

def test_mock_runner_output(sample_audio):
    """Test mock runner produces expected output."""
    runner = MockWhisperRunner(model="base", device="cpu")
    result = runner.run(sample_audio, language="en")
    
    # Verify structure
    assert "text" in result
    assert "segments" in result
    assert "language" in result
    assert "engine" in result
    
    # Verify content
    assert result["engine"] == "mock"
    assert result["language"] == "en"
    assert len(result["segments"]) == 2  # Mock always returns 2 segments
```

### Example 3: Testing Error Handling

```python
from tests.mock.runner import MockWhisperRunner

def test_mock_runner_file_not_found():
    """Test mock runner handles missing files."""
    runner = MockWhisperRunner()
    
    with pytest.raises(FileNotFoundError):
        runner.run("/nonexistent/file.wav")
```

### Example 4: Testing with Different Languages

```python
def test_transcribe_different_languages(use_mock_runner, sample_audio):
    """Test transcription with different language codes."""
    for lang in ["en", "fr", "es", "de"]:
        result = transcribe(
            f"job-{lang}",
            sample_audio,
            "whisperx",
            language=lang
        )
        assert result["language"] == lang
```

### Example 5: Testing Runner Factory

```python
from worker.tasks import get_runner
from worker.runners.whisperx import WhisperXRunner
from worker.runners.timestamped import TimestampedRunner

def test_get_runner_whisperx():
    """Test runner factory for WhisperX."""
    runner = get_runner("whisperx", "base")
    assert isinstance(runner, WhisperXRunner)
    assert runner.model == "base"

def test_get_runner_timestamped():
    """Test runner factory for timestamped."""
    runner = get_runner("timestamped", "small")
    assert isinstance(runner, TimestampedRunner)
    assert runner.model == "small"

def test_get_runner_invalid():
    """Test runner factory with invalid engine."""
    with pytest.raises(ValueError):
        get_runner("invalid_engine")
```

---

## Best Practices

### 1. **Use Fixtures for Integration Tests**

When testing the full `transcribe()` function, use the `use_mock_runner` fixture:

```python
def test_transcribe(use_mock_runner, sample_audio):
    # Clean and simple
    result = transcribe(...)
```

### 2. **Use Direct Mock for Unit Tests**

When testing runner logic in isolation, use `MockWhisperRunner` directly:

```python
def test_runner_logic(sample_audio):
    runner = MockWhisperRunner()
    result = runner.run(sample_audio)
    # Test specific behavior
```

### 3. **Test Both Success and Failure Cases**

Always test both happy paths and error conditions:

```python
def test_success(use_mock_runner, sample_audio):
    # Test successful transcription
    pass

def test_file_not_found(use_mock_runner):
    # Test error handling
    with pytest.raises(FileNotFoundError):
        transcribe("job-123", "/nonexistent.wav", "whisperx")
```

### 4. **Use Descriptive Test Names**

Follow the pattern: `test_<what>_<condition>_<expected_result>`

```python
def test_transcribe_with_whisperx_returns_mock_result():
    pass

def test_get_runner_with_invalid_engine_raises_value_error():
    pass
```

### 5. **Leverage Shared Fixtures**

Use fixtures from `conftest.py` instead of duplicating setup:

```python
# Good: Use shared fixture
def test_something(sample_audio):
    pass

# Bad: Create audio file in every test
def test_something(tmp_path):
    audio_file = tmp_path / "test.wav"
    # ... setup code
```

### 6. **Verify Mock Behavior**

When using patches, verify that functions were called correctly:

```python
@patch('worker.tasks.get_runner')
def test_transcribe_calls_runner(mock_get_runner, sample_audio):
    mock_runner = Mock()
    mock_runner.run.return_value = {...}
    mock_get_runner.return_value = mock_runner
    
    transcribe("job-123", sample_audio, "whisperx")
    
    mock_runner.run.assert_called_once()
    mock_get_runner.assert_called_once_with("whisperx", "base")
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_worker.py
```

### Run Specific Test Function

```bash
pytest tests/test_worker.py::test_transcribe_success
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=worker --cov-report=html
```

### Run Tests Matching Pattern

```bash
pytest -k "mock"  # Run all tests with "mock" in the name
```

---

## Understanding the Mock Output

The `MockWhisperRunner` always generates the same structure:

1. **Two segments** with timestamps
2. **Word-level timestamps** for each segment
3. **Text includes filename** (e.g., "from the file test_audio")
4. **Language** matches the provided parameter (defaults to "en")
5. **Engine** is always "mock"

**Example Mock Output:**
```python
{
    "text": "This is a mock transcription from the file test",
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "This is a mock transcription",
            "words": [
                {"word": "This", "start": 0.0, "end": 0.4},
                {"word": "is", "start": 0.5, "end": 0.7},
                {"word": "a", "start": 0.8, "end": 0.9},
                {"word": "mock", "start": 1.0, "end": 1.3},
                {"word": "transcription", "start": 1.4, "end": 2.5}
            ]
        },
        {
            "id": 1,
            "start": 2.5,
            "end": 5.0,
            "text": "from the file test",
            "words": [
                {"word": "from", "start": 2.5, "end": 2.8},
                {"word": "the", "start": 2.9, "end": 3.0},
                {"word": "file", "start": 3.1, "end": 3.4},
                {"word": "test", "start": 3.5, "end": 4.5}
            ]
        }
    ],
    "language": "en",
    "engine": "mock"
}
```

---

## Troubleshooting

### Issue: Mock not being used

**Solution:** Ensure you're using the fixture or patching correctly:

```python
# Make sure fixture is in function parameters
def test_something(use_mock_runner, sample_audio):
    pass
```

### Issue: FileNotFoundError in tests

**Solution:** Use the `sample_audio` fixture which creates a valid test file:

```python
def test_something(sample_audio):  # Use fixture
    runner = MockWhisperRunner()
    result = runner.run(sample_audio)  # Not a hardcoded path
```

### Issue: Tests failing with import errors

**Solution:** Ensure you're importing from the correct paths:

```python
# Correct
from tests.mock.runner import MockWhisperRunner
from tests.mock.factory import get_test_runner

# Incorrect (don't import from production code)
from worker.runners.mock import MockWhisperRunner  # This doesn't exist
```

### Issue: `fixture 'sample_audio' not found`

**Solution:** The `sample_audio` fixture is defined in `conftest.py`. If you see this error, ensure:
1. Your test file is in the `tests/` directory
2. You're including `sample_audio` in your test function parameters
3. The `conftest.py` file exists and contains the fixture

```python
# Correct - fixture is automatically available
def test_something(sample_audio):
    runner = MockWhisperRunner()
    result = runner.run(sample_audio)
```

### Issue: Test expects `FileNotFoundError` but gets `Exception`

**Solution:** The `transcribe()` function wraps exceptions. Use a more flexible assertion:

```python
# Instead of:
with pytest.raises(FileNotFoundError):
    transcribe("job-123", "/nonexistent/file.wav", "whisperx")

# Use:
with pytest.raises(Exception, match="Transcription failed.*Audio file not found"):
    transcribe("job-123", "/nonexistent/file.wav", "whisperx")
```

### Issue: Missing imports in test files

**Solution:** Ensure all required imports are present:

```python
# For tests using transcribe()
from worker.tasks import transcribe

# For tests using MockWhisperRunner
from tests.mock.runner import MockWhisperRunner

# For tests using get_test_runner
from tests.mock.factory import get_test_runner
from tests.mock.runner import MockWhisperRunner  # Also needed for isinstance checks
```

### Issue: Real runner tests failing with FileNotFoundError

**Solution:** When testing real runners (not mocks), create the audio file first:

```python
@patch('subprocess.run')
def test_whisperx_runner_success(mock_subprocess, tmp_path):
    # Create audio file first
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    
    # Then test the runner
    runner = WhisperXRunner()
    result = runner.run(str(audio_file))
```

---

## Summary

- **Use `use_mock_runner` fixture** for most integration tests
- **Use `MockWhisperRunner` directly** for unit tests of runner logic
- **Use `get_test_runner()`** when you need flexibility between mock and real
- **Use manual patching** when you need fine-grained control
- **Always test both success and failure cases**
- **Leverage shared fixtures** from `conftest.py`

The mock system is designed to make testing fast, reliable, and easy. Choose the approach that best fits your test's needs!

