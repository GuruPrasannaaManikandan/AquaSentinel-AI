# VERSION 4.8.6 — PRE-REPAIR BASELINE DIAGNOSTIC REPORT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.6 Pre-Repair Baseline Forensic Snapshot  
**Audit Date:** August 18, 2026  
**Status:** Pre-Repair Baseline Documented / Repair Phase Ready  

---

## 1. Initial Diagnostic Findings

### 1.1 C++ Firmware & PlatformIO IDE Audit
- **Observed Symptom**: `DriverFactory.h` and C++ drivers contained include path and signature IDE warnings/squiggles.
- **Root Cause**: Relative include paths (`../lib/MockDrivers/MockDrivers.h`) in `DriverFactory.cpp` and header resolution inconsistency across IDE workspace paths vs PlatformIO build environment.
- **Remediation Plan**: Standardize include directives across `firmware/include` and `firmware/lib` to use platform-agnostic include search paths.

### 1.2 Python Simulation API & Dashboard 400 Bad Request
- **Observed Symptom**:
  - Dashboard UI displays `"Step execution failed."`
  - Backend log displays: `POST /simulation/cycle HTTP/1.1 -> 400 Bad Request`
- **Root Cause**:
  - `BackendService.run_single_cycle()` in `src/backend/services.py` contained a hard validation check: `if self.simulation_active: raise ValueError("Cannot trigger single-step cycle while background simulation is active.")`.
  - When background simulation was started on demo launch, `run_single_cycle()` raised `ValueError`, causing `app.py` to return HTTP `400 Bad Request`.
  - Dashboard `fetch_json` helper displayed generic `"Step execution failed."` without extracting the exact error detail from the API response.
- **Remediation Plan**:
  - Update `BackendService.run_single_cycle()` to execute `_execute_cycle_locked(force=True)` safely using thread locking without rejecting active background simulation.
  - Update `fetch_json` and error handling in `dashboard/app.py` to extract and display backend error messages.

---

## 2. Pre-Repair System Baseline Metrics

- **pytest baseline**: 299 passed, 3 skipped (302 collected test items).
- **Phase 9 core assertions**: 244/244 passed.
- **V4 unit tests**: 58/58 passed.
- **V3.8 Frozen Files Protection**: 0 line modifications across all 5 frozen files (`src/iot/esp32_device.py`, `communication.py`, `scheduler.py`, `hal.py`, `actuators.py`).

---

## 3. Mandatory Architectural Boundaries

1. **Rule 1**: DO NOT START V4.9.
2. **Rule 2**: DO NOT IMPLEMENT PHYSICAL HARDWARE (Physical hardware remains `PENDING`).
3. **Rule 3**: SOFTWARE IS THE HARDWARE CONTRACT.
4. **Rule 4**: PROTECT FROZEN V3.8 FILES (0 line modifications).
5. **Rule 5**: DO NOT REMOVE FUNCTIONALITY OR WEAKEN TESTS.
6. **Rule 6**: PRESERVE V4.1 THROUGH V4.8.5 FUNCTIONALITY.
