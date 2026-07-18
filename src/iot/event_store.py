import sqlite3
import os
import json

# Intercept sqlite3.connect to automatically inject a 10-second busy timeout
_orig_connect = sqlite3.connect
def _timeout_connect(database, *args, **kwargs):
    kwargs.setdefault("timeout", 10.0)
    return _orig_connect(database, *args, **kwargs)
sqlite3.connect = _timeout_connect

class EventStore:
    """
    Persistence layer using SQLite to log the complete sensor-to-decision event lifecycle.
    Supports complete traceability for telemetry, validation, inference, actuators, and command histories.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # Default database location in workspace directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "models", "fusion", "aquatic_events.db")
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Telemetry logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                provenance_timestamp TEXT,
                device_id TEXT,
                latitude REAL,
                longitude REAL,
                temperature_c REAL,
                salinity_ppt REAL,
                ph REAL,
                turbidity_ntu REAL,
                dissolved_oxygen_mg_l REAL,
                wifi_connected INTEGER,
                mqtt_connected INTEGER,
                sensor_status TEXT
            )
        """)

        # Validation logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                is_valid INTEGER,
                errors TEXT,
                health_status TEXT
            )
        """)

        # Fusion decisions (ML + AIS + Fusion details)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fusion_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                ml_predicted_class TEXT,
                ml_confidence REAL,
                ml_dangerous_class INTEGER,
                ml_model_id TEXT,
                ais_is_anomaly INTEGER,
                ais_anomaly_score REAL,
                ais_matched_detectors INTEGER,
                ais_nearest_distance REAL,
                ais_model_id TEXT,
                final_state TEXT,
                reason_code TEXT,
                reasoning TEXT,
                confidence_band TEXT,
                fusion_version TEXT
            )
        """)

        # Actuator logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actuator_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                green_led TEXT,
                yellow_led TEXT,
                red_led TEXT,
                buzzer TEXT,
                pump_relay TEXT,
                event_desc TEXT
            )
        """)

        # Command logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                command TEXT,
                payload TEXT,
                status TEXT
            )
        """)

        # Error logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                error_msg TEXT
            )
        """)

        # Alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                severity TEXT,
                message TEXT,
                reason_code TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        # Check and alter telemetry_logs table dynamically to add provenance_timestamp if missing
        try:
            cursor.execute("SELECT provenance_timestamp FROM telemetry_logs LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE telemetry_logs ADD COLUMN provenance_timestamp TEXT")

        conn.commit()
        conn.close()

    def log_telemetry(self, t):
        """Logs device telemetry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO telemetry_logs (
                timestamp, provenance_timestamp, device_id, latitude, longitude, temperature_c, salinity_ppt,
                ph, turbidity_ntu, dissolved_oxygen_mg_l, wifi_connected, mqtt_connected, sensor_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t["timestamp"], t.get("provenance_timestamp"), t["device_id"], t["location"]["latitude"], t["location"]["longitude"],
            t["sensors"]["temperature_c"], t["sensors"]["salinity_ppt"], t["sensors"]["ph"],
            t["sensors"]["turbidity_ntu"], t["sensors"]["dissolved_oxygen_mg_l"],
            int(t["device_health"]["wifi_connected"]), int(t["device_health"]["mqtt_connected"]),
            t["device_health"]["sensor_status"]
        ))
        conn.commit()
        conn.close()

    def log_validation(self, timestamp, device_id, is_valid, errors, health):
        """Logs edge validation result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO validation_logs (timestamp, device_id, is_valid, errors, health_status)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, device_id, int(is_valid), json.dumps(errors), health))
        conn.commit()
        conn.close()

    def log_decision(self, d):
        """Logs gateway fusion decision."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fusion_decisions (
                timestamp, device_id, ml_predicted_class, ml_confidence, ml_dangerous_class, ml_model_id,
                ais_is_anomaly, ais_anomaly_score, ais_matched_detectors, ais_nearest_distance, ais_model_id,
                final_state, reason_code, reasoning, confidence_band, fusion_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["timestamp"], d["device_id"], str(d["ml_evidence"]["predicted_class"]),
            d["ml_evidence"]["confidence"], int(d["ml_evidence"]["dangerous_class"]), d["ml_evidence"]["model_id"],
            int(d["ais_evidence"]["is_anomaly"]), d["ais_evidence"]["anomaly_score"],
            d["ais_evidence"].get("matched_detector_count", 0), d["ais_evidence"].get("nearest_detector_distance", 999.0),
            d["ais_evidence"]["ais_model_id"], d["fusion"]["final_state"], d["fusion"]["reason_code"],
            d["fusion"]["reasoning"], d["fusion"]["confidence_band"], d["system_metadata"]["fusion_version"]
        ))
        conn.commit()
        conn.close()

    def log_actuators(self, timestamp, device_id, act_summary, event_desc):
        """Logs actuator transition event."""
        # Parse LEDs and Buzzer from summary string if needed
        # Format: LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF
        import re
        g = re.search(r"G=(\w+)", act_summary)
        y = re.search(r"Y=(\w+)", act_summary)
        r = re.search(r"R=(\w+)", act_summary)
        bz = re.search(r"Buzzer=(\w+)", act_summary)
        pm = re.search(r"Pump=(\w+)", act_summary)

        green = g.group(1) if g else "OFF"
        yellow = y.group(1) if y else "OFF"
        red = r.group(1) if r else "OFF"
        buzzer = bz.group(1) if bz else "OFF"
        pump = pm.group(1) if pm else "OFF"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO actuator_logs (timestamp, device_id, green_led, yellow_led, red_led, buzzer, pump_relay, event_desc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, device_id, green, yellow, red, buzzer, pump, event_desc))
        conn.commit()
        conn.close()

    def log_command(self, timestamp, device_id, command, payload, status):
        """Logs command channel event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO command_logs (timestamp, device_id, command, payload, status)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, device_id, command, json.dumps(payload), status))
        conn.commit()
        conn.close()

    def log_error(self, timestamp, device_id, error_msg):
        """Logs system error."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO error_logs (timestamp, device_id, error_msg)
            VALUES (?, ?, ?)
        """, (timestamp, device_id, error_msg))
        conn.commit()
        conn.close()

    # --- ALERT PERSISTENCE METHODS ---
    def log_alert(self, timestamp, device_id, severity, message, reason_code, acknowledged=0):
        """Persists a system alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, device_id, severity, message, reason_code, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, device_id, severity, message, reason_code, int(acknowledged)))
        conn.commit()
        conn.close()

    def get_alerts(self, device_id=None, acknowledged=None):
        """Retrieves list of persisted alerts with filtering options."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(int(acknowledged))
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def acknowledge_alert(self, alert_id):
        """Marks alert as acknowledged."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()

    # --- DATABASE QUERY LAYER METHODS ---
    def get_latest_telemetry(self, device_id):
        """Retrieves the latest telemetry for a device."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM telemetry_logs WHERE device_id = ? ORDER BY id DESC LIMIT 1
        """, (device_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_historical_telemetry(self, device_id, start_time=None, end_time=None):
        """Retrieves time-window filtered telemetry records."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM telemetry_logs WHERE device_id = ?"
        params = [device_id]
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        query += " ORDER BY id ASC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_latest_decision(self, device_id):
        """Retrieves the latest decision output for a device."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM fusion_decisions WHERE device_id = ? ORDER BY id DESC LIMIT 1
        """, (device_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_previous_decision(self, device_id, current_timestamp):
        """Retrieves the previous decision output for a device (excluding the current timestamp)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM fusion_decisions WHERE device_id = ? AND timestamp != ? ORDER BY id DESC LIMIT 1
        """, (device_id, current_timestamp))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_previous_telemetry(self, device_id, current_timestamp):
        """Retrieves the previous telemetry for a device (excluding the current timestamp)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM telemetry_logs WHERE device_id = ? AND timestamp != ? ORDER BY id DESC LIMIT 1
        """, (device_id, current_timestamp))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_historical_decisions(self, device_id, start_time=None, end_time=None):
        """Retrieves time-window filtered decisions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM fusion_decisions WHERE device_id = ?"
        params = [device_id]
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        query += " ORDER BY id ASC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_historical_actuators(self, device_id, start_time=None, end_time=None):
        """Retrieves historical actuator logs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM actuator_logs WHERE device_id = ?"
        params = [device_id]
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        query += " ORDER BY id ASC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_device_stats(self, device_id=None):
        """Aggregates system overview and health stats."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Telemetry total counts
        telemetry_q = "SELECT COUNT(*) FROM telemetry_logs"
        decisions_q = "SELECT COUNT(*) FROM fusion_decisions"
        warnings_q = "SELECT COUNT(*) FROM fusion_decisions WHERE final_state = 'WARNING'"
        criticals_q = "SELECT COUNT(*) FROM fusion_decisions WHERE final_state = 'CRITICAL'"
        anomalies_q = "SELECT COUNT(*) FROM fusion_decisions WHERE final_state = 'UNKNOWN_ANOMALY'"
        
        params = []
        if device_id:
            telemetry_q += " WHERE device_id = ?"
            decisions_q += " WHERE device_id = ?"
            warnings_q += " AND device_id = ?"
            criticals_q += " AND device_id = ?"
            anomalies_q += " AND device_id = ?"
            params.append(device_id)

        cursor.execute(telemetry_q, params)
        t_cnt = cursor.fetchone()[0]

        cursor.execute(decisions_q, params)
        d_cnt = cursor.fetchone()[0]

        cursor.execute(warnings_q, params)
        w_cnt = cursor.fetchone()[0]

        cursor.execute(criticals_q, params)
        c_cnt = cursor.fetchone()[0]

        cursor.execute(anomalies_q, params)
        a_cnt = cursor.fetchone()[0]

        # Sensor faults
        faults_q = "SELECT COUNT(*) FROM telemetry_logs WHERE sensor_status = 'FAULT'"
        if device_id:
            faults_q += " AND device_id = ?"
        cursor.execute(faults_q, params)
        f_cnt = cursor.fetchone()[0]

        conn.close()

        return {
            "total_telemetry": t_cnt,
            "total_decisions": d_cnt,
            "total_warnings": w_cnt,
            "total_criticals": c_cnt,
            "total_anomalies": a_cnt,
            "total_faults": f_cnt
        }

    def get_decision_by_timestamp(self, device_id, timestamp):
        """Retrieves the decision logged with the exact timestamp to prevent cycle mismatch."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM fusion_decisions WHERE device_id = ? AND timestamp = ?
        """, (device_id, timestamp))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_actuators_by_timestamp(self, device_id, timestamp):
        """Retrieves the actuator state logged with the exact timestamp, preferring actual device updates."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM actuator_logs WHERE device_id = ? AND timestamp = ? ORDER BY id DESC LIMIT 1
        """, (device_id, timestamp))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["summary"] = f"LEDs(G={row['green_led']}, Y={row['yellow_led']}, R={row['red_led']}), Buzzer={row['buzzer']}, Pump={row['pump_relay']}"
            return d
        return None

