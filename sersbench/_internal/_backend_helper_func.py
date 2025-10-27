from typing import Union, List, Dict, Any
from pathlib import Path
import json
import re

def _clean_json_datetimes(json_str):
    """Clean up datetime strings in JSON to proper ISO format"""
    def datetime_replacer(match):
        year, month, day, hour, minute, second = match.groups()
        return f'"{year}-{month.zfill(2)}-{day.zfill(2)}T{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}Z"'
    # Only fix datetime strings, don't mess with the JSON structure
    datetime_pattern = r'"datetime\.datetime\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)"'
    return re.sub(datetime_pattern, datetime_replacer, json_str)

def _safe_json_serializer(obj):
    """Custom JSON serializer that handles various datetime and other objects safely"""
    if hasattr(obj, 'isoformat'):
        # Handle datetime objects
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        # Handle objects with __dict__ (convert to dict)
        return obj.__dict__
    elif hasattr(obj, '_asdict'):
        # Handle namedtuples
        return obj._asdict()
    elif isinstance(obj, (set, frozenset)):
        # Handle sets
        return list(obj)
    elif isinstance(obj, complex):
        # Handle complex numbers
        return {"real": obj.real, "imag": obj.imag}
    else:
        # Fallback to string representation
        return str(obj)

def _load_calibration_data(data_dir: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load and parse calibration data from JSON files, removing duplicates."""
    data_path = Path(data_dir)
    json_files = list(data_path.glob("*.json"))
    if not json_files:
        return []
    
    calibrations = []
    seen_updates = set()
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            last_update = data["device_properties"]["last_update_date"]
            if last_update in seen_updates:
                continue
            seen_updates.add(last_update)
            
            cal_num = json_file.stem.split("d")[-1]
            calibrations.append({
                'calibration_number': cal_num,
                'last_update': last_update,
                'gates': data["device_properties"]["gates"],
                'file_path': str(json_file)
            })
            
        except (KeyError, IndexError, json.JSONDecodeError, FileNotFoundError):
            continue
    
    return sorted(calibrations, key=lambda x: x['calibration_number'])