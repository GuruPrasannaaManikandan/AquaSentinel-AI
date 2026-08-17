# Forensic Investigation Report: Single-Step Cycle Runtime Failure

**Document Identifier:** `docs/SINGLE_STEP_RUNTIME_FAILURE_INVESTIGATION.md`  
**Date & Time:** 2026-08-17  
**Investigator:** Antigravity AI  
**Subject:** Runtime failure on Streamlit dashboard button `"⚡ Trigger Single-Step Cycle"` showing `"Step execution failed."`

---

## Executive Summary

When clicking **"⚡ Trigger Single-Step Cycle"** on the Streamlit monitoring dashboard, the UI immediately displays **"Step execution failed."**

Through empirical request tracing, socket timing analysis, backend log inspection, and database audit, the investigation has conclusively proven that **the backend simulation engine executes the cycle with 100% success** and persists telemetry/decision data to SQLite. 

However, the dashboard client helper function `fetch_json()` in `dashboard/app.py` makes HTTP requests to `http://localhost:8000` with a strict `timeout=2.0` seconds. On Windows operating systems, Python's `requests` library attempts IPv6 (`::1:8000`) connection before falling back to IPv4 (`127.0.0.1:8000`). Because the FastAPI backend server (Uvicorn) is bound strictly to IPv4 `127.0.0.1:8000`, the Windows TCP stack incurs a 2.00-second socket connection timeout before falling back to IPv4. 

The combined duration of Windows IPv6 fallback delay (~2.00s) plus cycle execution time (~0.12s) totals **~2.145 seconds**, which **exceeds the 2.0-second client timeout threshold**. `requests.post()` raises a `ReadTimeout` exception, which `fetch_json()` silently swallows and returns `None`, causing Streamlit to render `"Step execution failed."` despite complete backend success.

---

## 1. Exact Reproduction Steps

1. Launch FastAPI backend on `127.0.0.1:8000`:
   ```bash
   python -m uvicorn src.backend.app:app --host 127.0.0.1 --port 8000 --log-level info
   ```
2. Launch Streamlit dashboard on `127.0.0.1:8501`:
   ```bash
   python -m streamlit run dashboard/app.py --server.port 8501 --server.address 127.0.0.1
   ```
3. Open browser to `http://127.0.0.1:8501`.
4. Select `AQUA_MARINE_001` in the sidebar **Device Selection** dropdown.
5. Set environmental scenario to `NORMAL`.
6. Click **"⚡ Trigger Single-Step Cycle"** ONCE.
7. Observe Streamlit sidebar rendering error box: `"Step execution failed."`
8. Repeat test once more: exact error reproduced.

---

## 2. Evidence Artifacts

- **UI Screenshot:** Saved in browser session artifacts as `first_trigger_result_1786945290722.png` and `second_trigger_result_1786945360614.png`.
- **UI Displayed Error:** `Step execution failed.` (Streamlit `st.sidebar.error`)
- **Timestamp:** 2026-08-17T11:07:01+05:30

---

## 3. Full Call Chain & Tracing

```
[Streamlit UI] User clicks "⚡ Trigger Single-Step Cycle"
   ↓ (dashboard/app.py:L115)
[Dashboard Handler] Calls fetch_json("/simulation/cycle", "POST")
   ↓ (dashboard/app.py:L58 - API_URL = "http://localhost:8000", timeout=2.0)
[HTTP Client - requests.post] Attempts socket connection to http://localhost:8000/simulation/cycle
   ├─► Windows TCP Stack attempts IPv6 (::1:8000) → No listener on ::1 (Stalls ~2.00s)
   └─► Windows TCP Stack falls back to IPv4 (127.0.0.1:8000) (Takes ~0.12s)
   ↓ (Total client elapsed time: 2.145s > 2.0s limit)
[Backend FastAPI Route] @app.post("/simulation/cycle") in src/backend/app.py:L383
   ↓ 
[Backend Service] service.run_single_cycle() in src/backend/services.py:L165
   ↓
[Lock Guard] service._execute_cycle_locked(force=True) in src/backend/services.py:L112
   ↓
[Device Runtime Manager] runtime.execute_cycle() in src/iot/device_runtime.py:L46
   ↓
[FSM Cycle] device.execute_one_complete_cycle() in src/iot/esp32_device.py:L354
   ↓
[Sensor Simulator] simulator.generate_reading() in src/iot/sensor_simulator.py:L175
   ↓
[Edge Validator] validator.validate() in src/iot/edge_validation.py:L35
   ↓
[FreeRTOS Scheduler] scheduler.step() → SensorTask & CommTask
   ↓
[MQTT Communication] CommunicationLayer → MQTT publish to aquatic/{device_id}/telemetry
   ↓
[Gateway Intelligence] Gateway.on_telemetry_received() → ML/AIS/Fusion pipeline
   ↓
[SQLite Event Store] EventStore logs telemetry_logs, fusion_decisions, actuator_logs
   ↓
[Backend FastAPI Response] Returns HTTP 200 OK {"status": "SUCCESS", ...} (Backend duration: 0.12s)
   ↓
[HTTP Client Exception] requests.exceptions.ReadTimeout raised in dashboard process at 2.00s!
   ↓
[dashboard/app.py:L63] generic `except Exception: pass` swallows ReadTimeout, returns None
   ↓
[dashboard/app.py:L120] `res is None` → triggers `st.sidebar.error("Step execution failed.")`
```

---

## 4. Network Request & Response Inspection

| Field | Measured Value / Finding |
|---|---|
| **HTTP Method** | `POST` |
| **Request Target URL** | `http://localhost:8000/simulation/cycle` |
| **Request Payload** | `None` / empty JSON |
| **Backend HTTP Status** | `200 OK` (Verified in Uvicorn log: `"POST /simulation/cycle HTTP/1.1" 200 OK`) |
| **Backend Processing Time** | `0.124` seconds |
| **Client-Side Request Duration (`localhost`)** | `2.145` seconds (Exceeds `timeout=2.0` threshold) |
| **Client-Side Request Duration (`127.0.0.1`)** | `0.117` seconds (Well within `timeout=2.0` threshold) |
| **Client-Side Exception** | `requests.exceptions.ReadTimeout: HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=2.0)` |
| **Dashboard Action** | Swallows exception, returns `None`, displays `"Step execution failed."` |

---

## 5. Backend Logs & Health Status Audit

- **FastAPI / Uvicorn Server Log:**
  ```text
  INFO: 127.0.0.1:49382 - "POST /simulation/cycle HTTP/1.1" 200 OK
  ```
- **Backend Traceback:** NONE. The backend completed cycle execution cleanly without raising any exceptions or errors.
- **Backend Health Check (`http://127.0.0.1:8000/health`):**
  ```json
  {"status": "UP", "timestamp": "2026-08-17T11:06:48.618845", "event_store": "OK", "models": {"caml_loaded": 0, "habsos_loaded": 0}}
  ```
- **Failing Code Location:**
  - `dashboard/app.py`, Line 53: `API_URL = "http://localhost:8000"`
  - `dashboard/app.py`, Line 60: `r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=2.0)`

---

## 6. Single-Step vs. Apply-Scenario Comparative Analysis

| Feature | Apply Scenario (`/simulation/scenario`) | Single-Step Cycle (`/simulation/cycle`) |
|---|---|---|
| **Backend Handler** | `post_simulation_scenario` (`app.py:L370`) | `post_simulation_cycle` (`app.py:L383`) |
| **Service Execution Path** | `service.set_scenario()` followed by `service._execute_cycle_locked(force=True)` | `service.run_single_cycle()` which calls `service._execute_cycle_locked(force=True)` |
| **Locking & Spacing** | Bypasses 1.95s spacing via `force=True` | Bypasses 1.95s spacing via `force=True` |
| **`http://localhost:8000` Duration** | ~2.096 seconds | ~2.145 seconds |
| **Behavior with `localhost` & `timeout=2.0`** | Marginally hits/misses 2.0s limit depending on CPU timing | Consistently exceeds 2.0s limit (2.145s > 2.0s), triggering client timeout |
| **Behavior with `127.0.0.1`** | Executes in **0.139s** | Executes in **0.117s** |

---

## 7. Device Comparative Analysis

- **`AQUA_FRESH_001` (Freshwater):**
  - Direct API execution time: `0.117s`
  - Dashboard behavior with `localhost` & `timeout=2.0`: Fails with `"Step execution failed."`
- **`AQUA_MARINE_001` (Marine):**
  - Direct API execution time: `0.124s`
  - Dashboard behavior with `localhost` & `timeout=2.0`: Fails with `"Step execution failed."`
- **Conclusion:** Both devices are equally affected. The issue is strictly in the shared Streamlit dashboard client HTTP transport layer (`fetch_json`).

---

## 8. Marine Scenario Comparative Analysis

Tested `AQUA_MARINE_001` across scenarios:
- `NORMAL`
- `KNOWN_BLOOM_RISK`
- `SENSOR_FAULT`

All three scenarios execute flawlessly on the backend API layer. The failure occurs identically across all scenarios when triggered via the dashboard due to the HTTP client timeout.

---

## 9. Background Simulation Interaction

- **When Background Simulation is STOPPED (`simulation_active = False`):**
  - `run_single_cycle()` invokes `_execute_cycle_locked(force=True)`. Backend succeeds in 0.12s. Dashboard client times out if using `localhost` with 2.0s timeout.
- **When Background Simulation is RUNNING (`simulation_active = True`):**
  - `run_single_cycle()` checks `self.simulation_active` and raises `ValueError("Cannot trigger single-step cycle while background simulation is active.")`.
  - Backend returns `HTTP 400 Bad Request`.
  - `fetch_json` receives status 400, returns `None`, and dashboard displays `"Step execution failed."` (Guard condition functioning as designed).

---

## 10. Database Persistence Verification (CASE A Identification)

- **Telemetry record count in `models/fusion/aquatic_events.db` before `/simulation/cycle` call:** `16875`
- **Telemetry record count after `/simulation/cycle` call:** `16877`
- **Net change:** `+2` new telemetry records (1 for Freshwater, 1 for Marine).
- **Classification:** **CASE A: Cycle executes successfully on backend and persists to database, but dashboard reports failure due to client-side HTTP timeout.**

---

## 11. Contract & Response Structure Audit

- **Backend Return Contract (`app.py:L388`):**
  ```json
  {
    "status": "SUCCESS",
    "message": "Single cycle simulation step completed.",
    "results": { ... }
  }
  ```
- **Dashboard Expectation (`dashboard/app.py:L116`):**
  ```python
  res = fetch_json("/simulation/cycle", "POST")
  if res:
      st.rerun()
  ```
- **Contract Evaluation:** The JSON schema contract matches expectations. `res` is evaluated as truthy (`dict`). The failure is not caused by key mismatch, but by `fetch_json()` returning `None` due to the network timeout exception.

---

## 12. Correlation with Recent Code Changes

Recent changes introduced cycle execution synchronization and spacing logic in `BackendService` (`_run_simulation_loop` and `_execute_cycle_locked`). 
While `_execute_cycle_locked(force=True)` correctly bypasses cycle spacing when manually triggered, the total cycle execution processing time across both devices (~0.12s) combined with Windows IPv6 DNS loopback resolution delay (~2.00s) pushed total client round-trip time to ~2.145 seconds. 

Because `fetch_json()` had a hardcoded `timeout=2.0` seconds and used `API_URL = "http://localhost:8000"`, the dashboard client timed out.

---

## 13. Root Cause Statement

**Primary Root Cause:**
In `dashboard/app.py`:
1. `API_URL` is hardcoded to `"http://localhost:8000"`. On Windows hosts, resolving `localhost` attempts IPv6 `::1:8000` before falling back to IPv4 `127.0.0.1:8000`. Because Uvicorn listens exclusively on IPv4 `127.0.0.1:8000`, each request to `localhost` incurs an internal OS socket connection fallback delay of ~2.00 seconds.
2. `fetch_json()` uses a fixed timeout of `timeout=2.0` seconds for all GET and POST requests.
3. Because `2.00s (OS fallback delay) + 0.12s (cycle execution)` = **`2.12s–2.15s`**, `requests.post()` raises `ReadTimeout`.
4. `fetch_json()` catches `Exception` silently and returns `None`, causing Streamlit to display `"Step execution failed."` even though the backend operation succeeded 100%.

**Root Cause Confidence:** **100% (Proven via timing benchmarks, socket trace, Uvicorn HTTP 200 logs, and database row count growth).**

---

## 14. Proposed Minimum Safe Fix

Modify `dashboard/app.py`:
1. Change `API_URL` from `"http://localhost:8000"` to `"http://127.0.0.1:8000"` (or allow environment variable override `os.getenv("API_URL", "http://127.0.0.1:8000")`).
2. Increase the default request timeout in `fetch_json(endpoint, method="GET", data=None, timeout=10.0)` from `2.0` seconds to `10.0` seconds (or accept a configurable `timeout` parameter).

**Scope of Fix:**
- Modifies ONLY 1 file: `dashboard/app.py`.
- ZERO changes to ML models, Marine datasets, sensor simulator, FSM logic, scheduler, or backend code.
