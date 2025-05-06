import subprocess
import os
import sys
import concurrent.futures

current_dir = os.getcwd()
utils_dir = os.path.join(current_dir, "scripts", "utils")  # Assuming "scripts" is the folder

if utils_dir not in sys.path:
    sys.path.append(utils_dir)

import welcome_screen as wc

scripts_dir = os.path.join(current_dir, "scripts")

# List of scripts to run in parallel
scripts = [
    "ibs.py",
    "ibs2.py",
    "smls.py",
    "ss.py",
    "k36.py",
]

def run_script(script):
    """
    Runs a single script via subprocess and returns a status message.
    This function is called in a separate process by ProcessPoolExecutor.
    """
    script_path = os.path.join(scripts_dir, script)

    if not os.path.exists(script_path):
        return f"❌ Script not found: {script_path}. Skipping..."

    # Use the virtual environment's Python interpreter
    python_executable = sys.executable  # This points to .venv/Scripts/python

    print(f"Running: {script_path} with {python_executable}...")

    # Run the script in a subprocess and capture its output
    process = subprocess.Popen(
        [python_executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # Ensures output is captured as strings
        encoding="utf-8",  # Explicitly set encoding to UTF-8
        env={**os.environ, "PYTHONUNBUFFERED": "1"},  # Add this line
    )

    # Prefix the output with the script name
    prefix = f"[{os.path.splitext(script)[0]}] "  # Extract script name without extension
    for line in process.stdout:
        print(f"{prefix}{line.strip()}", flush=True)  # Print each line with the prefix

    # Wait for the process to complete and capture errors
    process.wait()
    if process.returncode == 0:
        return f"✅ {script} completed successfully!"
    else:
        for line in process.stderr:
            print(f"{prefix}{line.strip()}", flush=True)  # Print errors with the prefix
        return f"❌ Error running {script}. Skipping to the next job..."

def run_scripts_in_parallel():
    """
    Runs all scripts in the `scripts` list concurrently using ProcessPoolExecutor.
    """
    # Create a pool of worker processes
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Submit each script to the process pool
        future_to_script = {
            executor.submit(run_script, script): script for script in scripts
        }

        # As each script finishes, print out its result
        for future in concurrent.futures.as_completed(future_to_script):
            script_name = future_to_script[future]
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"❌ {script_name} generated an exception: {e}")

# Start execution
if __name__ == "__main__":
    run_scripts_in_parallel()