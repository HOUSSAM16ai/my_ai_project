
from app.services.edge_multicloud.facade import EdgeMulticloudFacade

# Alias for compatibility if needed, or re-export
EdgeMultiCloudService = EdgeMulticloudFacade

_edge_service_instance = None

def get_edge_multicloud_service() -> EdgeMultiCloudService:
    global _edge_service_instance
    if _edge_service_instance is None:
        _edge_service_instance = EdgeMulticloudFacade()
    return _edge_service_instance
