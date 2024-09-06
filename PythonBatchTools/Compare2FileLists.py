import os

def compare_files(file1_path, file2_path, output_path):
    # Read the contents of both files
    with open(file1_path, 'r') as file1:
        file1_lines = set(file1.read().splitlines())
    
    with open(file2_path, 'r') as file2:
        file2_lines = set(file2.read().splitlines())
    
    # Find lines in file1 that are not in file2
    differences = file1_lines - file2_lines
    
    # Write the differences to the output file
    with open(output_path, 'w') as output_file:
        for line in sorted(differences):
            output_file.write(f"{line}\n")

# File paths
file1_path = 'filelist.txt'
file2_path = 'sorted_combined_paths.txt'
output_path = 'differences.txt'

# File paths
file1_path = r'C:/11111/filelist.txt'  # Use forward slashes and raw string
file2_path = r'C:/11111/sorted_combined_paths.txt'
output_path = r'C:/11111/differences.txt'

# Ensure the input files exist
if not os.path.exists(file1_path) or not os.path.exists(file2_path):
    print(f"Error: One or both input files do not exist.")
    print(f"file1_path: {file1_path}")
    print(f"file2_path: {file2_path}")
else:
    # Compare the files and write differences
    compare_files(file1_path, file2_path, output_path)
    print(f"Differences have been written to {output_path}")