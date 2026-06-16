# Event-Driven AI Incident Reporting API

This is a high-performance, event-driven backend built with **FastAPI** designed to handle emergency incident reports (e.g., fires, accidents, floods) from a mobile application. It processes images using AI, saves data to a cloud database, caches recent incidents for lightning-fast dashboards, and triggers real-time alerts.

## 🚀 Tech Stack

* **Framework:** FastAPI (Python)
* **AI Analysis:** Hugging Face Spaces (Grounding DINO object detection)
* **Primary Database:** Neon (Serverless PostgreSQL)
* **High-Speed Cache:** Upstash (Serverless Redis)
* **Event Bus:** FastAPI BackgroundTasks
* **Deployment:** Docker & Render.com

## 🧠 System Architecture

1. **Client Request:** A Flutter mobile app sends an image and GPS coordinates via `multipart/form-data` to the `/report` endpoint.
2. **AI Processing:** The backend forwards the image to a custom Hugging Face Space. Grounding DINO analyzes the image to detect the incident type and calculates a severity score.
3. **Immediate Response:** The backend instantly replies to the mobile app with a `200 OK` so the UI does not freeze.
4. **Event Processing (Background Consumers):** The data is tossed into an internal event bus which spins up 3 parallel workers:
   * **Storage Consumer:** Saves the complete incident record to Neon Postgres for long-term historical records.
   * **Cache Consumer:** Pushes the incident to Upstash Redis. (It strictly keeps only the 100 most recent incidents to ensure memory usage stays under 0.1 MB on the free tier).
   * **Notification Consumer:** Checks the severity score. If the incident is "high" or "critical", it triggers an immediate local desktop alert (which can easily be swapped back to Firebase FCM push notifications).

## 🛠️ Local Development Setup

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```ini
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   HF_URL=https://your-huggingface-space.hf.space/api/v1/incidents/analyze
   HF_TOKEN=your_token_if_private
   REDIS_URL=redis://default:password@host:port
   ```

4. **Run the Server:**
   ```bash
   uvicorn app:app --reload
   ```

5. **Test the Pipeline:**
   Run the automated test script to generate a fake image and send it through the whole pipeline:
   ```bash
   python test_api.py
   ```

## 📡 API Endpoints

### 1. `POST /report`
Receives an incident report from the mobile app.
* **Content-Type:** `multipart/form-data`
* **Body:**
  * `image` (File): The photo of the incident.
  * `latitude` (Float): GPS Latitude.
  * `longitude` (Float): GPS Longitude.

### 2. `GET /incidents`
Fetches the most recent incidents (e.g., for a police/fire department dashboard).
* Pulls directly from the lightning-fast Redis cache.
* Falls back to querying the PostgreSQL database if Redis is unavailable.

### 3. `GET /health`
Verifies that the server is online and successfully connected to the PostgreSQL database.

## ☁️ Deployment
This project includes a `Dockerfile` and is fully configured for free deployment on **Render.com** as a Web Service.
