# migration/auto_loop/loop_driver.py
import subprocess

from .auto_patch_builder import AutoPatchBuilder
from .file_migrator import FileMigrator


class LoopDriver:
    def __init__(self, codebase_path="app/"):
        self.codebase_path = codebase_path
        self.hotspots = []

    def find_hotspots(self):
        print("Scanning for Flask hotspots...")
        result = subprocess.run(
            ["grep", "-r", "-l", "from flask import", self.codebase_path],
            capture_output=True, text=True
        )
        files = result.stdout.strip().split('\n')
        self.hotspots = [
            f for f in files
            if f and 'compat_collapse' not in f and not f.endswith('.bak')
        ]
        print(f"Found {len(self.hotspots)} hotspots.")

    def run_full_migration(self):
        """
        Runs migration cycles on all found hotspots.
        """
        self.find_hotspots()

        if not self.hotspots:
            print("No Flask dependencies found to migrate.")
            return

        for target_file in self.hotspots:
            print(f"\n--- Processing: {target_file} ---")
            try:
                original_content = FileMigrator.read_file(target_file)
                if not original_content:
                    continue

                patched_content = AutoPatchBuilder.generate_patch(original_content)

                if patched_content != original_content:
                    FileMigrator.apply_patch(target_file, patched_content)
                else:
                    print("No changes needed.")

            except Exception as e:
                print(f"Error migrating {target_file}: {e}")

        print("\nFinished processing all hotspots.")


if __name__ == "__main__":
    driver = LoopDriver()
    driver.run_full_migration()
