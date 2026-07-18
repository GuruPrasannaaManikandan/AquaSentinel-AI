# Version 3.0 Handoff & Developer Guide (Computer Vision)

This handoff guide describes the frozen Version 2 structure, stable interfaces, and extension points to prepare for integrating **Version 3.0 (Computer Vision)**.

---

## 1. Frozen Code Boundaries (Do NOT Modify)

To respect backward compatibility contracts and the frozen release state of Version 2, developers must NOT alter:
1.  **AI Models State:** XGBoost and Random Forest classifiers, scaling models, and serialized negative selection detectors in `models/` are frozen.
2.  **Dempster-Shafer Math:** Do NOT alter the core weight combining mathematics in `DecisionPipeline`.
3.  **Microcontroller State Machine:** Core FSM states (`BOOT`, `ONLINE`, `SENSING`, `PUBLISHING`, `WAITING`, `ERROR`) are frozen.
4.  **Database Relational Schema:** The existing SQLite tables (`telemetry_logs`, `validation_logs`, `fusion_decisions`, `actuator_logs`, `alerts`) must remain backward compatible.

---

## 2. Core Extension Points for Computer Vision

### A. Camera Driver Integration (HAL)
*   **Location:** [sensors.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/drivers/sensors.py)
*   **Approach:** Implement `ESP32CameraDriver` derived from `BaseSensorDriver`.
*   **HAL Hook:** Instantiate and register the camera driver in `HAL.__init__()`:
    ```python
    self.sensors["camera"] = ESP32CameraDriver(pin=config.get_gpio().get("camera"))
    ```

### B. Scheduling Frame Inferences
*   **Location:** [esp32_device.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py)
*   **Approach:** Create a dedicated cooperative task `CameraTask` in `_register_rtos_tasks()`:
    ```python
    self.scheduler.register_task(
        Task(name="CameraTask", period_ticks=10, callback=self._camera_task_handler, priority=1)
    )
    ```
    *Note: Camera task execution period should be set to run less frequently (e.g. every 10 ticks) to prevent overloading the ESP32 CPU.*

### C. Backend Evidence Fusion Extension
*   **Location:** `src/fusion/decision_pipeline.py`
*   **Approach:** Extend `DempsterShafer` fusion equations to combine camera frame predictions (e.g. YOLO/MobileNet classification) as a third evidence source (`vision_evidence`), complementing supervised ML and unsupervised AIS outputs.

### D. EventStore Schema Additions
*   **Location:** [event_store.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/event_store.py)
*   **Approach:** Add `vision_logs` database table storing snapshot file paths, confidence levels, and identified object categories (e.g. algae bloom density, organic debris).

---

## 3. Recommended Roadmap for V3 Integration

1.  **Phase 3.1: Virtual Camera Driver.** Create mock frame generators that output random image buffers or load sample files.
2.  **Phase 3.2: Edge Frame Capture.** Schedule frame acquisitions in `CameraTask` and package image bytes into base64 payload arrays.
3.  **Phase 3.3: Backend Model Inference.** Deploy a YOLO or MobileNet classifier inside the FastAPI backend.
4.  **Phase 3.4: Evidence Fusion.** Combine image classification weights with the telemetry checks.
5.  **Phase 3.5: Dashboard Visualizer.** Display camera snapshot feeds in a new dashboard tab.
