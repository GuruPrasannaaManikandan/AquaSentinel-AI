import datetime

class AlertSystem:
    """
    Monitors telemetry and gateway fusion outcomes, automatically generating
    and persisting system-level alerts inside the EventStore.
    """
    @staticmethod
    def process_decision_for_alerts(decision, event_store):
        """Processes a fusion decision and triggers warning, critical, or anomaly alerts."""
        device_id = decision["device_id"]
        final_state = decision["fusion"]["final_state"]
        reason_code = decision["fusion"]["reason_code"]
        timestamp = decision.get("timestamp") or datetime.datetime.now().isoformat()

        if final_state in ["WARNING", "CRITICAL", "UNKNOWN_ANOMALY"]:
            last_dec = event_store.get_previous_decision(device_id, timestamp)
            last_state = last_dec["final_state"] if last_dec else "NORMAL"
            
            if last_state != final_state:
                severity = "HIGH" if final_state == "CRITICAL" else "MEDIUM"
                message = f"Fusion State: {final_state}. Reason: {decision['fusion']['reasoning']}"
                
                # Persist alert
                event_store.log_alert(
                    timestamp=timestamp,
                    device_id=device_id,
                    severity=severity,
                    message=message,
                    reason_code=reason_code,
                    acknowledged=0
                )

    @staticmethod
    def trigger_sensor_fault_alert(telemetry, errors, event_store):
        """Triggers alert when a physical sensor fault is flagged by edge validation."""
        timestamp = telemetry.get("timestamp") or datetime.datetime.now().isoformat()
        device_id = telemetry["device_id"]
        reason_code = "SENSOR_FAULT_ALERT"
        
        last_tel = event_store.get_previous_telemetry(device_id, timestamp)
        last_status = last_tel["sensor_status"] if last_tel else "OK"
        
        if last_status != "FAULT":
            message = f"Sensor Fault detected at edge. Errors: {', '.join(errors)}"
            
            event_store.log_alert(
                timestamp=timestamp,
                device_id=device_id,
                severity="HIGH",
                message=message,
                reason_code=reason_code,
                acknowledged=0
            )

    @staticmethod
    def trigger_device_offline_alert(device_id, last_seen, event_store):
        """Triggers alert if device heartbeat is missing."""
        timestamp = datetime.datetime.now().isoformat()
        reason_code = "DEVICE_OFFLINE_ALERT"
        message = f"Device {device_id} went offline. Last seen: {last_seen}"
        
        event_store.log_alert(
            timestamp=timestamp,
            device_id=device_id,
            severity="MEDIUM",
            message=message,
            reason_code=reason_code,
            acknowledged=0
        )

    @staticmethod
    def trigger_gateway_error_alert(device_id, error_msg, event_store):
        """Triggers alert on gateway pipeline errors."""
        timestamp = datetime.datetime.now().isoformat()
        reason_code = "GATEWAY_ERROR_ALERT"
        
        event_store.log_alert(
            timestamp=timestamp,
            device_id=device_id,
            severity="HIGH",
            message=f"Gateway pipeline crash: {error_msg}",
            reason_code=reason_code,
            acknowledged=0
        )
