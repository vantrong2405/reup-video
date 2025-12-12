import sys
from pathlib import Path
from utils.command_utils import CommandUtils

class UploadService:

    @staticmethod
    def upload_to_drive(local_path, drive_destination):
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"File to upload not found: {local_path}")

        print(f"Uploading {local_path} to {drive_destination}...")

        cmd = f"rclone copyto \"{local_path}\" \"{drive_destination}\" -P"

        try:
            CommandUtils.run_command(cmd)
            print(f"Upload successful: {drive_destination}")
            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            raise e

    @staticmethod
    def get_drive_link(drive_path):
        cmd = f"rclone link \"{drive_path}\""
        try:
            result = CommandUtils.run_command(cmd)
            link = result.stdout.strip()
            return link
        except Exception as e:
            print(f"Failed to get link for {drive_path}: {e}")
            return None
