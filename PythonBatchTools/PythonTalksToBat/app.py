import subprocess
import os

def run_batch_file(input_data):
    # Write input data to a file
    with open("input.txt", "w") as f:
        f.write(input_data)

    # Run the batch file
    result = subprocess.run(["example.bat", input_data], capture_output=True, text=True, shell=True)

    # Read the output file
    with open("output.txt", "r") as f:
        file_output = f.read()

    # Get environment variable
    env_output = os.environ.get("BATCH_RESULT")

    return {
        "stdout": result.stdout,
        "file_output": file_output,
        "env_output": env_output
    }

# Usage
results = run_batch_file("Hello from Python")
print("Standard output:", results["stdout"])
print("File output:", results["file_output"])
print("Environment variable:", results["env_output"])