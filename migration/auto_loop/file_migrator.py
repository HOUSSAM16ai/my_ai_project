# migration/auto_loop/file_migrator.py
"""
The File Migrator component of the AML.

This module is responsible for the low-level task of reading a file,
applying a generated patch, and writing the changes back.
"""
import os

class FileMigrator:
    @staticmethod
    def apply_patch(file_path: str, patch_content: str) -> bool:
        """
        Applies a patch to a file.

        For this simplified version, "applying a patch" means replacing
        the entire file content with the new, patched content. A real-world
        implementation would use a diffing library.
        """
        print(f"Applying patch to {file_path}...")
        try:
            # For safety, create a backup
            backup_path = f"{file_path}.bak"
            if os.path.exists(backup_path):
                print(f"Backup file {backup_path} already exists.")
            else:
                os.rename(file_path, backup_path)
                print(f"Created backup: {backup_path}")

            with open(file_path, "w") as f:
                f.write(patch_content)

            print(f"Successfully applied patch to {file_path}")
            return True
        except IOError as e:
            print(f"Error applying patch to {file_path}: {e}")
            # Attempt to restore from backup
            if os.path.exists(backup_path):
                os.rename(backup_path, file_path)
                print(f"Restored from backup: {file_path}")
            return False

    @staticmethod
    def read_file(file_path: str) -> str:
        """Reads the content of a file."""
        with open(file_path, "r") as f:
            return f.read()
