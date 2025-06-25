import os
import shutil
import argparse
import sys
from datetime import datetime

def clean_folder(folder_path, dry_run=False, log=False, log_entries=None):
    if not os.path.exists(folder_path):
        msg = f"Folder '{folder_path}' does not exist."
        print(msg)
        if log_entries is not None:
            log_entries.append(msg)
        return 0
    deleted = 0
    for entry in os.listdir(folder_path):
        entry_path = os.path.join(folder_path, entry)
        try:
            if os.path.isfile(entry_path) or os.path.islink(entry_path):
                action = f"Would delete file: {entry_path}" if dry_run else f"Deleted file: {entry_path}"
                print(action)
                if log_entries is not None:
                    log_entries.append(action)
                if not dry_run:
                    os.remove(entry_path)
                    deleted += 1
            elif os.path.isdir(entry_path):
                action = f"Would delete directory: {entry_path}" if dry_run else f"Deleted directory: {entry_path}"
                print(action)
                if log_entries is not None:
                    log_entries.append(action)
                if not dry_run:
                    shutil.rmtree(entry_path)
                    deleted += 1
        except Exception as e:
            err = f"Failed to delete {entry_path}: {e}"
            print(err)
            if log_entries is not None:
                log_entries.append(err)
    summary = f"{'Would delete' if dry_run else 'Cleanup complete.'} {deleted} items {'would be' if dry_run else ''} deleted from '{folder_path}'."
    print(summary)
    if log_entries is not None:
        log_entries.append(summary)
    return deleted

def clean_all(dry_run=False, log=False, yes=False, folder=None):
    log_entries = [] if log else None
    folders = [folder] if folder else ['darkSecureFolder', 'c2_data']
    total_deleted = 0
    for f in folders:
        print(f"\nCleaning folder: {f}")
        if log_entries is not None:
            log_entries.append(f"\nCleaning folder: {f}")
        total_deleted += clean_folder(f, dry_run=dry_run, log=log, log_entries=log_entries)
    if log and log_entries:
        with open('clean_dark_secure_folder.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- {datetime.now()} ---\n")
            for line in log_entries:
                f.write(line + '\n')
    print(f"\nTotal items deleted: {total_deleted}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean all files and subdirectories inside darkSecureFolder and c2_data.")
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted, but do not delete.')
    parser.add_argument('--log', action='store_true', help='Log deletions to clean_dark_secure_folder.log.')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt.')
    parser.add_argument('--folder', type=str, default=None, help='Target folder to clean (default: both darkSecureFolder and c2_data).')
    args = parser.parse_args()

    if not args.yes:
        if args.folder:
            confirm = input(f"Are you sure you want to delete all contents of '{args.folder}'? (y/N): ").strip().lower()
        else:
            confirm = input("Are you sure you want to delete all contents of 'darkSecureFolder' and 'c2_data'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    clean_all(dry_run=args.dry_run, log=args.log, yes=args.yes, folder=args.folder) 