from src.iot.drivers.base_driver import BaseActuatorDriver

class VirtualLEDDriver(BaseActuatorDriver):
    """Virtual LED driver representing a GPIO-controlled visual status indicator."""
    def __init__(self, name: str, pin: int = None, config: dict = None):
        super().__init__(name, pin, config)

    def set_state(self, state: str) -> bool:
        success = super().set_state(state)
        if success:
            # We can log or print here to mock a physical state write
            pass
        return success


class VirtualBuzzerDriver(BaseActuatorDriver):
    """Virtual Buzzer driver representing a GPIO-controlled sound alarm."""
    def __init__(self, name: str, pin: int = None, config: dict = None):
        super().__init__(name, pin, config)

    def set_state(self, state: str) -> bool:
        success = super().set_state(state)
        if success:
            pass
        return success


class VirtualRelayDriver(BaseActuatorDriver):
    """Virtual Relay driver representing a GPIO-controlled power switch (e.g. for pump/aerator)."""
    def __init__(self, name: str, pin: int = None, config: dict = None):
        super().__init__(name, pin, config)

    def set_state(self, state: str) -> bool:
        success = super().set_state(state)
        if success:
            pass
        return success
