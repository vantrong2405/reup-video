import subprocess
import os

input_file = "src/assets/video/video-origin.mp4"
logo_file = "src/assets/img/image_new.png"
output_file = "downloads/debug_out.mp4"

def run(name, cmd):
    print(f"\n--- Running {name} ---")
    print(cmd)
    try:
        if os.path.exists(output_file): os.unlink(output_file)
        subprocess.check_call(cmd, shell=True)
        print("SUCCESS")
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e}")

# Test Metadata with single quotes inside double quotes
cmd_meta = (
    f"ffmpeg -v error -y -i {input_file} "
    f"-metadata comment='Processed by N8N Auto - 1234' "
    f"-c copy {output_file}"
)

# Test Noise Filter
cmd_noise = (
    f"ffmpeg -v error -y -i {input_file} "
    f"-filter_complex \"noise=c0s=1:allf=t:u=123\" "
    f"-c:v libx264 -preset veryfast {output_file}"
)

run("Metadata Syntax", cmd_meta)
run("Noise Syntax", cmd_noise)
