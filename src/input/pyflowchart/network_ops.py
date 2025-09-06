class APIError(Exception):
    pass

class ConnectionError(Exception):
    pass

class DataHandler:
    def __init__(self, base_url, api_key=None, timeout=30, max_retries=3):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = "requests_session"
    
    def fetch_data(self, endpoint, params=None, method='GET', data=None, headers=None):
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        url = f"{self.base_url}/{endpoint}"
        request_headers = {"Accept": "application/json"}
        
        if headers:
            request_headers.update(headers)
        
        retries = 0
        
        while retries <= self.max_retries:
            try:
                print(f"Making {method} request to {url}")
                
                if method.upper() == 'GET':
                    response = {"status": 200, "data": {"result": "success"}}
                elif method.upper() == 'POST':
                    response = {"status": 201, "data": {"result": "created"}}
                elif method.upper() == 'PUT':
                    response = {"status": 200, "data": {"result": "updated"}}
                elif method.upper() == 'DELETE':
                    response = {"status": 204, "data": None}
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response["status"] >= 400:
                    raise APIError(f"API returned HTTP {response['status']}")
                
                return response["data"]
                
            except APIError as e:
                if retries < self.max_retries:
                    wait_time = 2 ** retries
                    print(f"API error, retrying in {wait_time}s... ({retries+1}/{self.max_retries})")
                    retries += 1
                    continue
                raise
                
            except Exception as e:
                if retries < self.max_retries:
                    wait_time = 2 ** retries
                    print(f"Connection error, retrying in {wait_time}s... ({retries+1}/{self.max_retries})")
                    retries += 1
                    continue
                
                raise ConnectionError(f"Failed to connect to API: {str(e)}")
        
        raise ConnectionError(f"Maximum retries ({self.max_retries}) exceeded")
    
    def close(self):
        print("Closing session")