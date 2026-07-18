import os
import re
import pandas as pd
import numpy as np

class SeaBASSParser:
    def __init__(self):
        self.metadata = {}
        self.comments = []
        self.fields = []
        self.units = []
        self.missing_value = None
        self.below_detection_limit = None
        self.delimiter = ","
        self.warnings = []

    def parse(self, filepath):
        """
        Parses a SeaBASS .sb file and returns (metadata, comments, dataframe).
        """
        self.metadata = {}
        self.comments = []
        self.fields = []
        self.units = []
        self.missing_value = None
        self.below_detection_limit = None
        self.delimiter = ","
        self.warnings = []

        filename = os.path.basename(filepath)
        self.metadata["source_file"] = filename

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        header_started = False
        header_ended = False
        data_lines = []

        for line_num, line in enumerate(lines, 1):
            line_str = line.strip()
            
            # Check for header bounds
            if line_str == "/begin_header":
                header_started = True
                continue
            if line_str == "/end_header":
                header_ended = True
                continue

            if not header_ended:
                # Inside header
                if line_str.startswith("!"):
                    # Comment line
                    comment_val = line_str[1:].strip()
                    self.comments.append(comment_val)
                    continue
                if line_str.startswith("/"):
                    # Metadata key-value
                    match = re.match(r"^/([a-zA-Z0-9_]+)=(.*)$", line_str)
                    if match:
                        key = match.group(1).strip()
                        val = match.group(2).strip()
                        self.metadata[key] = val
                    else:
                        self.warnings.append(f"Line {line_num}: Malformed metadata line '{line_str}'")
            else:
                # Inside data section
                if line_str:  # Skip empty lines
                    data_lines.append((line_num, line_str))

        # Check header status
        if not header_started:
            raise ValueError(f"Missing '/begin_header' in file {filename}")
        if not header_ended:
            raise ValueError(f"Missing '/end_header' in file {filename}")

        # Post-process header metadata
        if "fields" in self.metadata:
            self.fields = [f.strip() for f in self.metadata["fields"].split(",")]
        else:
            raise ValueError(f"Missing '/fields' definition in header of {filename}")

        if "units" in self.metadata:
            self.units = [u.strip() for u in self.metadata["units"].split(",")]
        else:
            raise ValueError(f"Missing '/units' definition in header of {filename}")

        if len(self.fields) != len(self.units):
            self.warnings.append(
                f"Field count ({len(self.fields)}) does not match unit count ({len(self.units)}). "
                f"Fields: {self.fields}, Units: {self.units}"
            )

        if "missing" in self.metadata:
            try:
                self.missing_value = float(self.metadata["missing"])
            except ValueError:
                self.missing_value = self.metadata["missing"]
                self.warnings.append(f"Non-numeric missing value code: {self.missing_value}")

        if "below_detection_limit" in self.metadata:
            try:
                self.below_detection_limit = float(self.metadata["below_detection_limit"])
            except ValueError:
                self.below_detection_limit = self.metadata["below_detection_limit"]

        if "delimiter" in self.metadata:
            delim_val = self.metadata["delimiter"].lower()
            if delim_val == "comma":
                self.delimiter = ","
            elif delim_val == "tab":
                self.delimiter = "\t"
            elif delim_val == "space":
                self.delimiter = " "
            else:
                self.warnings.append(f"Unknown delimiter '{delim_val}', defaulting to comma.")
                self.delimiter = ","

        # Parse tabular data
        parsed_data = []
        expected_cols = len(self.fields)

        for line_num, data_line in data_lines:
            # Handle comments inside data (though rare in SeaBASS)
            if data_line.startswith("!"):
                continue
            
            # Split line
            if self.delimiter == " ":
                # Space delimiter could mean multiple spaces
                parts = [p.strip() for p in data_line.split() if p.strip()]
            else:
                parts = [p.strip() for p in data_line.split(self.delimiter)]

            if len(parts) != expected_cols:
                self.warnings.append(
                    f"Line {line_num}: Column count mismatch. Expected {expected_cols}, got {len(parts)}. Row content: '{data_line}'"
                )
                # We do not discard; pad or truncate
                if len(parts) < expected_cols:
                    parts += [""] * (expected_cols - len(parts))
                else:
                    parts = parts[:expected_cols]

            parsed_data.append(parts)

        # Create DataFrame
        df = pd.DataFrame(parsed_data, columns=self.fields)

        # Attempt to convert numeric columns to float, replacing missing value flags with NaN
        for col in df.columns:
            # Check if this is a coordinate or datetime column that might need special treatment
            if col in ["date", "time", "station", "bottle", "sample", "hplc_gsfc_id"]:
                continue
            
            # Convert to numeric where possible
            try:
                numeric_series = pd.to_numeric(df[col], errors="coerce")
                
                # Replace missing codes and below-detection-limit codes with NaN or custom representations
                if self.missing_value is not None:
                    numeric_series = numeric_series.replace(self.missing_value, np.nan)
                if self.below_detection_limit is not None:
                    # Note: below detection limit can be kept or set to 0/NaN depending on analysis.
                    # We will replace below detection limit flags with NaN or keep them as -8888 for later imputation.
                    # For statistical analysis, we'll keep them as NaN or 0.0 in clean data. We'll set to NaN for numeric calculations.
                    numeric_series = numeric_series.replace(self.below_detection_limit, np.nan)
                    
                df[col] = numeric_series
            except Exception as e:
                self.warnings.append(f"Failed to convert column '{col}' to numeric: {str(e)}")

        return self.metadata, self.comments, df, self.warnings
