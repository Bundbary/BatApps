# Open the input file and read the lines
with open(r'c:\Users\bpenn\Downloads\combined_paths.txt', 'r') as file:
    lines = file.readlines()

# Sort the lines alphabetically
sorted_lines = sorted(lines)

# Write the sorted lines to a new output file
with open(r'c:\Users\bpenn\Downloads\sorted_combined_paths.txt', 'w') as file:
    file.writelines(sorted_lines)

print("Lines have been sorted and written to 'sorted_combined_paths.txt'.")