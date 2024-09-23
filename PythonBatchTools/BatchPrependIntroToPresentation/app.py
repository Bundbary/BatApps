import subprocess
import os
import json
import tempfile

def get_video_duration(file_path):
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])


def merge_videos(input1, input2, output, fade_duration=2):
    temp_dir = os.path.dirname(input1)
    temp_file1 = os.path.join(temp_dir, "temp1.ts")
    temp_file2 = os.path.join(temp_dir, "temp2.ts")
    last_frame_file = os.path.join(temp_dir, "last_frame.png")
    fade_out_file = os.path.join(temp_dir, "fade_out.ts")
    list_file = os.path.join(temp_dir, "temp_file_list.txt")

    try:
        # Steps 1-2: Convert inputs to TS format (unchanged)
        for input_file, temp_file in [(input1, temp_file1), (input2, temp_file2)]:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-c', 'copy',
                '-bsf:v', 'h264_mp4toannexb',
                '-f', 'mpegts',
                temp_file
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Step 3: Extract last frame from input2
        cmd = [
            'ffmpeg',
            '-i', input2,
            '-vf', 'select=\'eq(n,0)\'',
            '-vframes', '1',
            last_frame_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Step 4: Create fade-out clip
        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', last_frame_file,
            '-t', str(fade_duration),
            '-vf', f'fade=t=out:st=0:d={fade_duration}',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-f', 'mpegts',
            fade_out_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Step 5: Create list file (modified to include fade-out clip)
        with open(list_file, "w") as f:
            f.write(f"file '{os.path.basename(temp_file1)}'\n")
            f.write(f"file '{os.path.basename(temp_file2)}'\n")
            f.write(f"file '{os.path.basename(fade_out_file)}'\n")

        # Step 6: Concatenate (unchanged)
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-y', output
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=temp_dir)
        print("FFmpeg output:")
        print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
        raise
    finally:
        # Clean up temporary files
        for file in [temp_file1, temp_file2, last_frame_file, fade_out_file, list_file]:
            if os.path.exists(file):
                os.remove(file)

def process_folder(folder_path):
    global_props = os.path.join(folder_path, 'global_props.mp4')
    output = os.path.join(folder_path, 'output.mp4')
    presentation = os.path.join(folder_path, 'presentation.mp4')

    if not os.path.exists(global_props) or not os.path.exists(output):
        print(f"Error: Missing required files in {folder_path}")
        return False

    try:
        print(f"Processing folder: {folder_path}")
        print("Checking input file durations...")
        duration1 = get_video_duration(global_props)
        duration2 = get_video_duration(output)
        print(f"Duration of global_props.mp4: {duration1:.2f} seconds")
        print(f"Duration of output.mp4: {duration2:.2f} seconds")
        print(f"Total expected duration: {duration1 + duration2:.2f} seconds")

        print("Merging videos...")
        merge_videos(global_props, output, presentation, fade_duration=2)
        print("Checking output file duration...")
        output_duration = get_video_duration(presentation)
        print(f"Duration of merged output: {output_duration:.2f} seconds")

        if abs((duration1 + duration2) - output_duration) > 1:  # Allow 1 second tolerance
            print("Warning: Output duration doesn't match the sum of input durations!")
        else:
            print("Output duration matches expected duration.")

        print(f"Videos merged successfully. Output saved as: {presentation}")
        return True
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return False

def batch_process(root_folder):
    success_count = 0
    error_count = 0
    total_folders = sum(1 for _, dirs, _ in os.walk(root_folder) if 'backup' not in dirs)
    processed_folders = 0

    for root, dirs, files in os.walk(root_folder):
        dirs[:] = [d for d in dirs if 'backup' not in d.lower()]
        
        if 'global_props.mp4' in files and 'output.mp4' in files:
            processed_folders += 1
            print(f"\nProgress: {processed_folders}/{total_folders} folders")
            if process_folder(root):
                success_count += 1
            else:
                error_count += 1

    print(f"\nBatch processing complete.")
    print(f"Total folders processed: {processed_folders}")
    print(f"Successful merges: {success_count}")
    print(f"Errors encountered: {error_count}")

if __name__ == "__main__":
    root_folder = input("Enter the path to the root folder: ").strip()
    batch_process(root_folder)