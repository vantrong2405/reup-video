import os
import shutil
import re
from utils.command_utils import CommandUtils

class FileUtils:
    @staticmethod
    def download_file(url, output_path):
        print(f"Downloading from {url} to {output_path}")
        if url.startswith("file://"):
            local_path = url[7:]
            if os.path.exists(local_path):
                 shutil.copy(local_path, output_path)
                 return
        elif os.path.exists(url):
             shutil.copy(url, output_path)
             return

        final_url = url
        if "drive.google.com" in url:
            file_id = None
            match = re.search(r'/d/([^/]*)/', url)
            if match:
                file_id = match.group(1)
            else:
                match = re.search(r'[?&]id=([^&]*)', url)
                if match:
                    file_id = match.group(1)

            if not file_id and re.match(r'^[a-zA-Z0-9_-]+$', url):
                 file_id = url

            if file_id:
                final_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        cmd = f"wget -O \"{output_path}\" \"{final_url}\""
        CommandUtils.run_command(cmd)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception(f"Downloaded file is empty or not found: {output_path}")
