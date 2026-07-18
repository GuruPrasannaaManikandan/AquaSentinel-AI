class BaseSensorDriver:
    """
    Abstract base class for all sensor drivers in the embedded system.
    Defines a standard interface for hardware initialization and reading telemetry.
    """
    def __init__(self, name: str, pin: int = None, config: dict = None):
        self.name = name
        self.pin = pin
        self.config = config or {}
        self.status = "OK"  # "OK" or "FAULT"

    def init(self) -> bool:
        """
        Initializes the physical or virtual sensor.
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        self.status = "OK"
        return True

    def read(self):
        """
        Reads value from the sensor.
        Returns:
            The raw sensor value (numeric, string, or tuple).
        """
        raise NotImplementedError("Subclasses must implement read()")


class BaseActuatorDriver:
    """
    Abstract base class for all actuator drivers in the embedded system.
    Defines a standard interface for writing state to a physical or virtual output pin.
    """
    def __init__(self, name: str, pin: int = None, config: dict = None):
        self.name = name
        self.pin = pin
        self.config = config or {}
        self.state = "OFF"  # "ON" or "OFF"

    def set_state(self, state: str) -> bool:
        """
        Sets the actuator state.
        Args:
            state (str): "ON" or "OFF"
        Returns:
            bool: True if successful, False otherwise.
        """
        if state not in ["ON", "OFF"]:
            return False
        self.state = state
        return True

    def get_state(self) -> str:
        """
        Gets the current state of the actuator.
        Returns:
            str: "ON" or "OFF"
        """
        return self.state
