def parse_response_json(response):
    try:
        return response.json()
    except Exception:
        import json
        return json.loads(response.content)
