import os
import urllib.request
import urllib.error
import urllib.parse
import json
import time

def log_operation(api_key, action, description=None, file_id=None, file_name=None, operation_type=None):
    if not api_key:
        print("ERROR: No API key provided for logging")
        return False

    # Ensure action has pdf- prefix
    if not action.startswith('pdf-'):
        action = f"pdf-{action}"

    # Prepare data
    data = {
        'action': action,
        'description': description or f"{action} operation on {file_name or 'a file'}",
        'fileId': file_id,
        'fileName': file_name,
        'operationType': operation_type or action.replace('pdf-', '')
    }

    # Convert data to JSON string
    data_json = json.dumps(data).encode('utf-8')

    # Debug output
    print(f"[PDF-LOGGER] Sending log with API key: {api_key[:10]}... for action: {action}")

    try:
        # Backend API URL
        backend_url = os.environ.get('BACKEND_URL', 'http://backend:3000/api')
        log_url = f"{backend_url}/pdfLogs/log"

        # Create request
        req = urllib.request.Request(
            url=log_url,
            data=data_json,
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': api_key
            },
            method='POST'
        )

        # Send request
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            print(f"[PDF-LOGGER] Log response: {response_data}")
            if response.status == 200:
                print(f"[PDF-LOGGER] Operation logged successfully: {action}")
                return True
            else:
                print(f"[PDF-LOGGER] Failed to log operation: {response.status}")
                return False
    except Exception as e:
        print(f"[PDF-LOGGER] Error: {str(e)}")

        # Try alternative endpoint
        try:
            history_log_url = f"{backend_url}/history/log"
            history_req = urllib.request.Request(
                url=history_log_url,
                data=json.dumps({
                    'action': action,
                    'description': description or f"{action} operation on {file_name or 'a file'}",
                    'metadata': {
                        'fileId': file_id,
                        'fileName': file_name,
                        'operationType': operation_type or action.replace('pdf-', '')
                    }
                }).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {api_key}"
                },
                method='POST'
            )

            with urllib.request.urlopen(history_req) as response:
                response_data = response.read().decode('utf-8')
                print(f"[PDF-LOGGER] Backup log response: {response_data}")
                if response.status == 200:
                    print(f"[PDF-LOGGER] Operation logged via backup endpoint: {action}")
                    return True
        except Exception as backup_error:
            print(f"[PDF-LOGGER] Backup logging failed: {str(backup_error)}")

        return False