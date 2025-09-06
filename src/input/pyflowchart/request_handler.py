REQUEST_STATUS_PENDING = "pending"
REQUEST_STATUS_PROCESSING = "processing"
REQUEST_STATUS_COMPLETED = "completed"
REQUEST_STATUS_FAILED = "failed"
REQUEST_STATUS_INVALID = "invalid"

REQUEST_TYPE_GET_DATA = "get_data"
REQUEST_TYPE_CREATE_RESOURCE = "create_resource"
REQUEST_TYPE_UPDATE_RESOURCE = "update_resource"
REQUEST_TYPE_DELETE_RESOURCE = "delete_resource"
REQUEST_TYPE_PROCESS_DATA = "process_data"
REQUEST_TYPE_GENERATE_REPORT = "generate_report"
REQUEST_TYPE_SYSTEM_COMMAND = "system_command"

requests_store = {}

def _validate_request(request):
    request_type = request["request_type"]
    data = request["data"]
    
    if request_type == REQUEST_TYPE_GET_DATA:
        if 'resource' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_CREATE_RESOURCE:
        if 'resource_type' not in data or 'resource_data' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_UPDATE_RESOURCE:
        if 'resource_id' not in data or 'resource_data' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_DELETE_RESOURCE:
        if 'resource_id' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_PROCESS_DATA:
        if 'data' not in data or 'operation' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_GENERATE_REPORT:
        if 'report_type' not in data:
            return False
            
    elif request_type == REQUEST_TYPE_SYSTEM_COMMAND:
        if 'command' not in data:
            return False
        
        allowed_commands = ['status', 'refresh', 'restart', 'backup']
        if data['command'] not in allowed_commands:
            return False
    
    return True

def _authorize_request(request):
    user_id = request["user_id"]
    request_type = request["request_type"]
    data = request["data"]
    
    if user_id.startswith('admin-'):
        return True
    
    if request_type == REQUEST_TYPE_SYSTEM_COMMAND:
        return False
    
    if request_type in [REQUEST_TYPE_GET_DATA, REQUEST_TYPE_GENERATE_REPORT]:
        return True
    
    if request_type == REQUEST_TYPE_PROCESS_DATA:
        if 'user_id' in data and data['user_id'] == user_id:
            return True
    
    if request_type == REQUEST_TYPE_CREATE_RESOURCE:
        return True
    
    if request_type in [REQUEST_TYPE_UPDATE_RESOURCE, REQUEST_TYPE_DELETE_RESOURCE]:
        if 'owner_id' in data and data['owner_id'] == user_id:
            return True
    
    return False

def _handle_request_by_type(request):
    request_type = request["request_type"]
    data = request["data"]
    
    if request_type == REQUEST_TYPE_GET_DATA:
        resource = data.get('resource')
        return {"resource": resource, "data": ["item1", "item2"]}
        
    elif request_type == REQUEST_TYPE_CREATE_RESOURCE:
        resource_type = data.get('resource_type')
        return {"resource_id": "new_id", "resource_type": resource_type}
        
    elif request_type == REQUEST_TYPE_UPDATE_RESOURCE:
        resource_id = data.get('resource_id')
        return {"resource_id": resource_id, "updated": True}
        
    elif request_type == REQUEST_TYPE_DELETE_RESOURCE:
        resource_id = data.get('resource_id')
        return {"resource_id": resource_id, "deleted": True}
        
    elif request_type == REQUEST_TYPE_PROCESS_DATA:
        operation = data.get('operation')
        return {"operation": operation, "result": "processed"}
        
    elif request_type == REQUEST_TYPE_GENERATE_REPORT:
        report_type = data.get('report_type')
        return {"report_type": report_type, "data": {"summary": "report data"}}
        
    elif request_type == REQUEST_TYPE_SYSTEM_COMMAND:
        command = data.get('command')
        return {"command": command, "status": "executed"}
    
    return {"error": "Unknown request type"}

def create_request(request_type, data, user_id, priority=1):
    request_id = f"req_{len(requests_store) + 1}"
    
    request = {
        "request_id": request_id,
        "request_type": request_type,
        "data": data,
        "user_id": user_id,
        "priority": priority,
        "status": REQUEST_STATUS_PENDING,
        "created_at": "timestamp",
        "processed_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    requests_store[request_id] = request
    return request_id

def get_request(request_id):
    return requests_store.get(request_id)

def handle_request(request_id):
    request = get_request(request_id)
    
    if request is None:
        print(f"Request {request_id} not found")
        return False
    
    if request["status"] not in [REQUEST_STATUS_PENDING, REQUEST_STATUS_FAILED]:
        print(f"Request {request_id} is already in status {request['status']}")
        return False
    
    try:
        request["status"] = REQUEST_STATUS_PROCESSING
        request["processed_at"] = "timestamp"
        
        print(f"Processing request {request_id} of type {request['request_type']}")
        
        if not _validate_request(request):
            request["status"] = REQUEST_STATUS_INVALID
            request["error"] = "Invalid request data"
            print(f"Request {request_id} has invalid data: {request['data']}")
            return False
        
        if not _authorize_request(request):
            request["status"] = REQUEST_STATUS_FAILED
            request["error"] = "Unauthorized request"
            print(f"User {request['user_id']} is not authorized for request {request_id}")
            return False
        
        result = _handle_request_by_type(request)
        
        request["result"] = result
        request["status"] = REQUEST_STATUS_COMPLETED
        request["completed_at"] = "timestamp"
        
        print(f"Request {request_id} completed successfully")
        return True
        
    except Exception as e:
        request["status"] = REQUEST_STATUS_FAILED
        request["error"] = str(e)
        request["completed_at"] = "timestamp"
        
        print(f"Error processing request {request_id}: {str(e)}")
        return False

if __name__ == "__main__":
    req_id = create_request(
        request_type=REQUEST_TYPE_GET_DATA,
        data={"resource": "users"},
        user_id="user-123"
    )
    
    success = handle_request(req_id)
    print(f"Request handling success: {success}")