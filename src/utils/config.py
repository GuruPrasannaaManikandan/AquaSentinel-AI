import os
import yaml

class Config:
    """
    Configuration manager to load and parse YAML settings.
    Provides simple helper methods to get values.
    """
    def __init__(self, config_path=None):
        if config_path is None:
            # Locate relative to workspace root
            # Assume config.yaml is in a folder 'config' inside the workspace root
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(base_dir, "config", "config.yaml")

        self.config_path = config_path
        self._config = {}
        self.load()

    def load(self):
        """Loads or reloads the YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            try:
                self._config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML file at {self.config_path}: {e}")

    def get(self, key, default=None):
        """Get top-level config values."""
        return self._config.get(key, default)

    def get_path(self, path_key, default=None):
        """Convenience to fetch paths section."""
        return self._config.get("paths", {}).get(path_key, default)

    def get_dataset_config(self, dataset_name):
        """Fetch config for a specific dataset, e.g., 'caml' or 'habsos'."""
        return self._config.get("datasets", {}).get(dataset_name, {})

    @property
    def random_seed(self):
        return self._config.get("project", {}).get("random_seed", 42)
