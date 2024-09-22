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

def merge_videos(input1, input2, output):
    temp_dir = os.path.dirname(input1)
    temp_file1 = os.path.join(temp_dir, "temp1.ts")
    temp_file2 = os.path.join(temp_dir, "temp2.ts")
    list_file = os.path.join(temp_dir, "temp_file_list.txt")

    try:
        # Convert to TS format
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

        # Create list file
        with open(list_file, "w") as f:
            f.write(f"file '{os.path.basename(temp_file1)}'\n")
            f.write(f"file '{os.path.basename(temp_file2)}'\n")

        # Concatenate
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
    finally:
        # Clean up temporary files
        for file in [temp_file1, temp_file2, list_file]:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    input1 = input("Enter the path of the first video file: ").strip()
    input2 = input("Enter the path of the second video file: ").strip()
    output = os.path.join(os.path.dirname(input1), 'merged_output.mp4')

    try:
        print("Checking input file durations...")
        duration1 = get_video_duration(input1)
        duration2 = get_video_duration(input2)
        print(f"Duration of {input1}: {duration1:.2f} seconds")
        print(f"Duration of {input2}: {duration2:.2f} seconds")
        print(f"Total expected duration: {duration1 + duration2:.2f} seconds")

        print("Merging videos...")
        merge_videos(input1, input2, output)

        print("Checking output file duration...")
        output_duration = get_video_duration(output)
        print(f"Duration of merged output: {output_duration:.2f} seconds")

        if abs((duration1 + duration2) - output_duration) > 1:  # Allow 1 second tolerance
            print("Warning: Output duration doesn't match the sum of input durations!")
        else:
            print("Output duration matches expected duration.")

        print(f"Videos merged successfully. Output saved as: {output}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")