import os
import requests
import base64

def run_test():
    # Use the live Render URL
    API_URL = "https://event-back-brfc.onrender.com"
    
    img_path = "test_image.jpg"
    if not os.path.exists(img_path):
        print("Generating sample image...")
        b64_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(b64_png))

    print(f"Testing root endpoint ({API_URL}/)...")
    try:
        health_resp = requests.get(f"{API_URL}/")
        print("Health Check:", health_resp.json())
    except Exception as e:
        print("Health check failed:", e)

    print(f"\nTesting /report endpoint...")
    try:
        with open(img_path, "rb") as f:
            files = {"image": ("test_image.jpg", f, "image/jpeg")}
            data = {"latitude": 37.7749, "longitude": -122.4194}
            report_resp = requests.post(f"{API_URL}/report", files=files, data=data)
            print("Status Code:", report_resp.status_code)
            try:
                print("Response:", report_resp.json())
            except Exception:
                print("Text response:", report_resp.text)
    except Exception as e:
        print("Report failed:", e)
        
    print(f"\nTesting /incidents endpoint...")
    try:
        inc_resp = requests.get(f"{API_URL}/incidents")
        print("Incidents Count:", inc_resp.json().get("count"))
    except Exception as e:
        print("Incidents check failed:", e)

if __name__ == "__main__":
    run_test()
