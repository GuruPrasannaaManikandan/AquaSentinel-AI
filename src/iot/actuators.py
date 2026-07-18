class VirtualActuators:
    """
    Simulates physical edge-side actuators including indicators (LEDs), sound alarm (Buzzer),
    and a relay-controlled virtual aerator/pump.
    """
    def __init__(self):
        self.green_led = "OFF"
        self.yellow_led = "OFF"
        self.red_led = "OFF"
        self.buzzer = "OFF"
        self.pump_relay = "OFF"
        self.actuator_logs = []

    def update_state(self, fusion_state):
        """
        Maps final system decision state to physical actuator outputs.
        NORMAL          -> Green LED ON, others OFF
        WARNING         -> Yellow LED ON, Pump ON, others OFF
        CRITICAL        -> Red LED ON, Buzzer ON, Pump ON, others OFF
        UNKNOWN_ANOMALY -> Yellow/Red ON, others OFF (requires manual inspection)
        """
        old_state = self.get_summary()

        if fusion_state == "NORMAL":
            self.green_led = "ON"
            self.yellow_led = "OFF"
            self.red_led = "OFF"
            self.buzzer = "OFF"
            self.pump_relay = "OFF"
        elif fusion_state == "WARNING":
            self.green_led = "OFF"
            self.yellow_led = "ON"
            self.red_led = "OFF"
            self.buzzer = "OFF"
            self.pump_relay = "ON" # Simulated pump/aerator activation for water circulation
        elif fusion_state == "CRITICAL":
            self.green_led = "OFF"
            self.yellow_led = "OFF"
            self.red_led = "ON"
            self.buzzer = "ON" # Sound alarm triggered
            self.pump_relay = "ON"
        elif fusion_state == "UNKNOWN_ANOMALY":
            self.green_led = "OFF"
            self.yellow_led = "ON"
            self.red_led = "ON" # Both LEDs flag unusual OOD state
            self.buzzer = "OFF"
            self.pump_relay = "OFF" # Deactivated to prevent potential chemical dispersing
        else:
            # Fallback/Error state
            self.green_led = "OFF"
            self.yellow_led = "ON"
            self.red_led = "ON"
            self.buzzer = "ON"
            self.pump_relay = "OFF"

        new_state = self.get_summary()
        if old_state != new_state:
            log_entry = f"Actuator transitioned to: {new_state} (State: {fusion_state})"
            self.actuator_logs.append(log_entry)

    def execute_command(self, cmd_type):
        """Executes hardware-override commands from command channel."""
        if cmd_type == "ACTIVATE_BUZZER":
            self.buzzer = "ON"
        elif cmd_type == "DEACTIVATE_BUZZER":
            self.buzzer = "OFF"
        elif cmd_type == "ACTIVATE_RELAY":
            self.pump_relay = "ON"
        elif cmd_type == "DEACTIVATE_RELAY":
            self.pump_relay = "OFF"
        else:
            return False
        
        self.actuator_logs.append(f"Manual Override executed: {cmd_type}")
        return True

    def get_summary(self):
        """Returns string representation of current actuator states."""
        return f"LEDs(G={self.green_led}, Y={self.yellow_led}, R={self.red_led}), Buzzer={self.buzzer}, Pump={self.pump_relay}"
