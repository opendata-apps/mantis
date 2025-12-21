import subprocess
import sys
import threading
import os
import signal
import platform
from app import create_app


def handle_vite_output(process):
    rebuilding = False
    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line:
            line = line.strip()
            if "Rebuilding..." in line or "build started" in line:
                if not rebuilding:
                    print("\033[36mVite:\033[0m Rebuilding...", flush=True)
                    rebuilding = True
            elif "Done in" in line or "built in" in line:
                print(f"\033[36mVite:\033[0m {line}", flush=True)
                rebuilding = False


def start_vite_watch():
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        try:
            process = subprocess.Popen(
                "bun run watch",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,
            )
            print("\033[36mStarted Vite build watcher\033[0m")
            output_thread = threading.Thread(
                target=handle_vite_output, args=(process,), daemon=True
            )
            output_thread.start()
            return process
        except Exception as e:
            print(
                f"\033[31mFailed to start Vite watcher: {e}\033[0m",
                file=sys.stderr,
            )
            return None
    return None


def cleanup_process(process):
    if process and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        try:
            if process.poll() is None:
                if platform.system() == "Windows":
                    process.terminate()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"\033[31mError stopping Vite: {e}\033[0m")
        finally:
            process.wait()
            print("\033[36m\nStopped Vite watcher\033[0m")


app = create_app()

if __name__ == "__main__":
    vite_process = start_vite_watch()

    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        if vite_process:
            cleanup_process(vite_process)