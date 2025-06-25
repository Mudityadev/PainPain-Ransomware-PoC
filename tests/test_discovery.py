import pytest
from ransomware.discovery.discoverer import FileDiscoverer


def test_discover_files(tmp_path):
    # Create some files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("test1")
    file2.write_text("test2")

    discoverer = FileDiscoverer(str(tmp_path))
    files = discoverer.discover_files()

    assert len(files) == 2
    assert any("file1.txt" in f for f in files)
    assert any("file2.txt" in f for f in files)

