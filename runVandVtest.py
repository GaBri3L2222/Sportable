import subprocess
import sys

def run_script(script_path):
    print(f"\n=== Running {script_path} ===")
    result = subprocess.run([sys.executable, script_path])
    
    if result.returncode != 0:
        print(f"ERROR : Error while running {script_path}")
    else:
        print(f"SUCCESS : {script_path} completed successfully")

if __name__ == "__main__":
    run_script("tests/test_verification_env.py")
    run_script("tests/test_validation_pose.py")
    run_script("tests/test_validation_network.py")

    print("\n=== V&V Testing Completed ===")