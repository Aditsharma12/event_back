import os
import time
import subprocess
import requests

def run_test():
    img_path = "test_image.jpg"
    if not os.path.exists(img_path):
        print("Generating sample image...")
        import base64
        # valid 1x1 PNG
        b64_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(b64_png))

    print("Starting FastAPI server...")
    # Start the server using uvicorn
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"
        
    process = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app:app", "--port", "8000"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(5)
    
    print("Testing /health endpoint...")
    try:
        health_resp = requests.get("http://127.0.0.1:8000/health")
        print("Health Check:", health_resp.json())
    except Exception as e:
        print("Health check failed:", e)

    print("Testing /report endpoint...")
    try:
        with open(img_path, "rb") as f:
            files = {"image": ("test_image.jpg", f, "image/jpeg")}
            data = {
                "latitude": 37.7749,
                "longitude": -122.4194
            }
            report_resp = requests.post("http://127.0.0.1:8000/report", files=files, data=data)
            print("Status Code:", report_resp.status_code)
            try:
                print("Response:", report_resp.json())
            except Exception:
                print("Text response:", report_resp.text)
    except Exception as e:
        print("Report failed:", e)
        
    print("Testing /incidents endpoint...")
    try:
        inc_resp = requests.get("http://127.0.0.1:8000/incidents")
        print("Incidents Count:", inc_resp.json().get("count"))
    except Exception as e:
        print("Incidents check failed:", e)

    print("Shutting down server...")
    process.terminate()
    process.wait()
    
    # print any stderr from server if it failed
    stderr = process.stderr.read().decode('utf-8')
    if stderr:
        print("\n--- Server Stderr (if any) ---")
        print(stderr)

if __name__ == "__main__":
    run_test()
