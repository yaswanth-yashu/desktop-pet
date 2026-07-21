import subprocess
import sys

def run_npm_install():
    print("Running npm install via Python subprocess...")
    try:
        # Using shell=True for windows npm command lookup
        result = subprocess.run(["npm", "install"], capture_output=True, text=True, shell=True)
        print("--- stdout ---")
        print(result.stdout)
        print("--- stderr ---")
        print(result.stderr)
        print(f"Exit code: {result.returncode}")
        if result.returncode == 0:
            print("[✓] npm install completed successfully.")
        else:
            print("[!] npm install failed.")
    except Exception as e:
        print(f"[!] Error running subprocess: {e}")

if __name__ == "__main__":
    run_npm_install()
