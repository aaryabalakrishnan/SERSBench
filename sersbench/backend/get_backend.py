import json
import re
# NOTE: qiskit version 1.0.2
# Migration guide: https://docs.quantum.ibm.com/api/migration-guides/qiskit-1.0-features#qiskitcircuit
# https://docs.quantum.ibm.com/api/migration-guides/qiskit-1.0-features#execute
# from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_runtime import (
    QiskitRuntimeService,
)  # https://docs.quantum.ibm.com/verify/cloud-based-simulators#qasm-simulator
from qiskit_ibm_runtime import QiskitRuntimeService
from datetime import datetime, timedelta
import platform
import logging
from sersbench._internal import _safe_json_serializer, _clean_json_datetimes

logger = logging.getLogger(__name__)

def get_current_backend(
    token: str,
    instance: str,
    save_path: str = None,
    backend_name: str = 'ibm_brisbane',
    start_date: datetime = datetime.now(),
    end_date: datetime = datetime.now()
):
    """
    Retrieve IBM backend device properties for a date range.

    If save_path is provided, saves JSON files to disk and returns list of filenames.
    If not, returns list of device property JSON dicts.

    Args:
        token (str): IBM Quantum API token.
        instance (str): IBM Quantum instance name.
        save_path (str, optional): Path to save JSON files. If None, data is returned.
        backend_name (str, optional): Backend name (default 'ibm_brisbane').
        start_date (datetime, optional): Start datetime (default now).
        end_date (datetime, optional): End datetime (default now).

    Returns:
        List[str] if save_path is provided, else List[dict].
    """
    try:
        QiskitRuntimeService.save_account(
            token=token,
            instance=instance,
            overwrite=True
        )
        service = QiskitRuntimeService()

        if save_path and platform.system() == 'Windows':
            save_path = save_path.replace("\\", "/")

        backend = service.backend(backend_name)

        # If start_date and end_date are date objects, convert to datetime
        if hasattr(start_date, 'date') and not hasattr(start_date, 'hour'):
            current = datetime.combine(start_date, datetime.min.time())
        else:
            current = start_date
            
        if hasattr(end_date, 'date') and not hasattr(end_date, 'hour'):
            end_dt = datetime.combine(end_date, datetime.min.time())
        else:
            end_dt = end_date

        result = []

        while current <= end_dt:
            try:
                # Pass the datetime object directly to the backend.properties() method
                props = backend.properties(datetime=current)
                
                # Convert properties to dict safely
                if props is None:
                    logger.warning(f"No properties found for {backend_name} on {current}")
                    props_dict = {"error": f"No properties available for {current}"}
                else:
                    props_dict = props.to_dict()
                
                data = {"device_properties": props_dict}
                
                # First attempt: use custom serializer
                try:
                    json_str = json.dumps(data, default=_safe_json_serializer, indent=4)
                except (TypeError, ValueError) as e:
                    logger.warning(f"First serialization attempt failed for {current}: {e}")
                    # Second attempt: convert everything to string
                    try:
                        json_str = json.dumps(data, default=str, indent=4)
                    except (TypeError, ValueError) as e2:
                        logger.error(f"Second serialization attempt failed for {current}: {e2}")
                        # Create a minimal error response
                        error_data = {
                            "device_properties": {
                                "error": f"Serialization failed: {str(e2)}",
                                "backend": backend_name,
                                "date": str(current),
                                "last_update_date": str(current)
                            }
                        }
                        json_str = json.dumps(error_data, indent=4)
                
                # Clean up datetime strings
                cleaned = _clean_json_datetimes(json_str)
                
                # Parse back to ensure it's valid JSON
                try:
                    final_data = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for {current}: {e}")
                    # Create a safe fallback
                    final_data = {
                        "device_properties": {
                            "error": f"JSON decode failed: {str(e)}",
                            "backend": backend_name,
                            "date": str(current),
                            "last_update_date": str(current)
                        }
                    }

                if save_path:
                    current_date = current.date() if hasattr(current, 'date') else current
                    filename = f"{save_path}/{backend_name}_{current_date}.json"
                    with open(filename, "w") as f:
                        f.write(json.dumps(final_data, indent=4))
                    result.append(filename)
                else:
                    result.append(final_data)

            except Exception as date_error:
                logger.error(f"Error processing date {current} for backend {backend_name}: {date_error}")
                # Create error entry for this date
                error_data = {
                    "device_properties": {
                        "error": f"Date processing failed: {str(date_error)}",
                        "backend": backend_name,
                        "date": str(current),
                        "last_update_date": str(current)
                    }
                }
                
                if save_path:
                    current_date = current.date() if hasattr(current, 'date') else current
                    filename = f"{save_path}/{backend_name}_{current_date}_error.json"
                    with open(filename, "w") as f:
                        f.write(json.dumps(error_data, indent=4))
                    result.append(filename)
                else:
                    result.append(error_data)

            current += timedelta(days=1)

        return result

    except Exception as e:
        logger.error(f"Critical error in get_current_backend: {e}", exc_info=True)
        # Return a list with a single error entry
        error_data = {
            "device_properties": {
                "error": f"Backend retrieval failed: {str(e)}",
                "backend": backend_name,
                "date_range": f"{start_date} to {end_date}",
                "last_update_date": str(datetime.now())
            }
        }
        return [error_data]