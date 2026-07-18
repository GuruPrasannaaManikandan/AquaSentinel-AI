# Security Review Report

This report presents a capstone-level security audit of the integrated software simulation.

## 1. Audited Security Boundaries

### 1.1 REST API Validation & Parameterization
*   **FastAPI Inputs:** All parameters use Pydantic models (e.g. `CommandRequestSchema`) restricting types, lengths, and formats. Invalid payloads are rejected with `422 Unprocessable Entity` responses.
*   **SQL Parameters:** All SQLite interactions in [event_store.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/event_store.py) use parameterized queries (e.g. `SELECT * FROM telemetry_logs WHERE device_id = ?`). No string concatenation is used, neutralizing SQL injection vectors.

### 1.2 IoT Device Registry Authorization
*   **Authentication:** The central gateway maintains a locked list of authorized device IDs. Telemetry from unregistered devices is rejected before model or decision pipeline processing.

### 1.3 CORS & Web Security
*   **CORS Configuration:** Standard middleware allows all origins (`*`) for Streamlit dashboard client requests. 
*   **Path Traversal:** Device lookup endpoints strictly validate IDs against Pydantic string patterns, preventing folder navigation attacks (e.g., `device_id = "../../etc/passwd"`).
*   **Deserialization:** Model loading uses `joblib.load()`. We implement strict validation before calling `joblib.load` by checking that target files exist within authorized project folders (`models/deployment/` or `models/ais/`) and verifying filenames in the locked manifests.

---

## 2. Capstone Scope & Disclaimer

This system is a **software simulation capstone project** and is **not** certified for production deployment. The API runs without transport-layer encryption (HTTPS) or OAuth2 authentication tokens, and the MQTT adapter runs in-memory.
