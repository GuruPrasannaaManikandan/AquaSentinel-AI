import subprocess
import sys
import time
import os

def main():
    print("==============================================================")
    print("🌊 STARTING AQUATIC ECOSYSTEM IoT & AIS MONITORING DEMO 🌊")
    print("==============================================================")
    
    # Resolve directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Start FastAPI Backend
    print("[1/2] Launching FastAPI Backend Server via Uvicorn...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "src.backend.app:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "info"
    ]
    
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=base_dir,
        text=True
    )

    # Give backend server 2 seconds to bind port
    time.sleep(2.0)

    # 2. Start Streamlit Dashboard
    print("[2/2] Launching Streamlit Visualization Dashboard...")
    dashboard_cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard/app.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1"
    ]
    
    dashboard_proc = subprocess.Popen(
        dashboard_cmd,
        cwd=base_dir,
        text=True
    )

    print("\n🎉 DEMO RUNNING SUCCESSFULLY!")
    print("👉 Access the API Documentation: http://127.0.0.1:8000/docs")
    print("👉 Access the Monitoring Dashboard: http://127.0.0.1:8501")
    print("\nPress Ctrl+C to terminate both servers and stop simulation.")

    try:
        # Keep process alive and forward brief console logs if helpful
        while True:
            # Check backend output briefly
            backend_code = backend_proc.poll()
            if backend_code is not None:
                print(f"Error: FastAPI backend terminated unexpectedly with exit code {backend_code}.")
                break
            dashboard_code = dashboard_proc.poll()
            if dashboard_code is not None:
                print(f"Error: Streamlit dashboard terminated unexpectedly with exit code {dashboard_code}.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping demo servers and cleaning up background runtimes...")
    finally:
        # Graceful shutdowns
        dashboard_proc.terminate()
        backend_proc.terminate()
        try:
            dashboard_proc.wait(timeout=2.0)
            backend_proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            dashboard_proc.kill()
            backend_proc.kill()
        print("Demo cleanup completed. Safe to exit.")

if __name__ == "__main__":
    main()
