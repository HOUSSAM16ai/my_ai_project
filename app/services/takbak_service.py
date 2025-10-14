"""
Takbak Service - تطبيق خدمة الطبقات
====================================
A utility service for managing layers/tabaqat in the educational AI platform.

This service provides layer management functionality for organizing content,
AI models, or educational hierarchies.

الغرض (Purpose):
خدمة بسيطة لإدارة الطبقات والتنظيم الهرمي للمحتوى التعليمي
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, UTC


class TakbakService:
    """
    Service for managing hierarchical layers (tabaqat/طبقات)
    
    This service helps organize content into layers for better structure
    and navigation in the educational platform.
    """
    
    def __init__(self):
        """Initialize the Takbak service"""
        self.layers: Dict[str, Dict[str, Any]] = {}
    
    def create_layer(
        self,
        layer_id: str,
        name: str,
        description: str = "",
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new layer in the hierarchy
        
        Args:
            layer_id: Unique identifier for the layer
            name: Display name of the layer
            description: Optional description
            parent_id: Optional parent layer ID for hierarchical structure
            metadata: Additional metadata
            
        Returns:
            Dict containing the created layer information
        """
        if layer_id in self.layers:
            raise ValueError(f"Layer with ID '{layer_id}' already exists")
        
        if parent_id and parent_id not in self.layers:
            raise ValueError(f"Parent layer '{parent_id}' not found")
        
        layer = {
            "id": layer_id,
            "name": name,
            "description": description,
            "parent_id": parent_id,
            "metadata": metadata or {},
            "created_at": datetime.now(UTC).isoformat(),
            "children": []
        }
        
        self.layers[layer_id] = layer
        
        # Update parent's children list
        if parent_id:
            self.layers[parent_id]["children"].append(layer_id)
        
        return layer
    
    def get_layer(self, layer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a layer by ID
        
        Args:
            layer_id: The layer identifier
            
        Returns:
            Layer dictionary or None if not found
        """
        return self.layers.get(layer_id)
    
    def list_layers(
        self,
        parent_id: Optional[str] = None,
        include_children: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all layers, optionally filtered by parent
        
        Args:
            parent_id: Optional parent ID to filter by
            include_children: Whether to include child layer information
            
        Returns:
            List of layer dictionaries
        """
        if parent_id is None:
            # Return all root layers (no parent)
            result = [
                layer for layer in self.layers.values()
                if layer["parent_id"] is None
            ]
        else:
            # Return children of specific parent
            if parent_id not in self.layers:
                return []
            result = [
                self.layers[child_id]
                for child_id in self.layers[parent_id]["children"]
            ]
        
        if not include_children:
            # Remove children info from result
            result = [
                {k: v for k, v in layer.items() if k != "children"}
                for layer in result
            ]
        
        return result
    
    def update_layer(
        self,
        layer_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing layer
        
        Args:
            layer_id: The layer to update
            name: New name (optional)
            description: New description (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated layer dictionary
        """
        if layer_id not in self.layers:
            raise ValueError(f"Layer '{layer_id}' not found")
        
        layer = self.layers[layer_id]
        
        if name is not None:
            layer["name"] = name
        if description is not None:
            layer["description"] = description
        if metadata is not None:
            layer["metadata"].update(metadata)
        
        layer["updated_at"] = datetime.now(UTC).isoformat()
        
        return layer
    
    def delete_layer(self, layer_id: str, cascade: bool = False) -> bool:
        """
        Delete a layer
        
        Args:
            layer_id: The layer to delete
            cascade: If True, delete all children recursively
            
        Returns:
            True if deleted successfully
        """
        if layer_id not in self.layers:
            return False
        
        layer = self.layers[layer_id]
        
        # Handle children
        if layer["children"]:
            if not cascade:
                raise ValueError(
                    f"Layer '{layer_id}' has children. "
                    "Use cascade=True to delete them."
                )
            # Delete children recursively
            for child_id in layer["children"][:]:  # Copy to avoid modification during iteration
                self.delete_layer(child_id, cascade=True)
        
        # Remove from parent's children list
        if layer["parent_id"]:
            parent = self.layers[layer["parent_id"]]
            parent["children"].remove(layer_id)
        
        # Delete the layer
        del self.layers[layer_id]
        
        return True
    
    def get_hierarchy(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the complete hierarchy tree
        
        Args:
            root_id: Optional root layer ID. If None, returns all root layers
            
        Returns:
            Hierarchical tree structure
        """
        def build_tree(layer_id: str) -> Dict[str, Any]:
            layer = self.layers[layer_id].copy()
            layer["children"] = [
                build_tree(child_id)
                for child_id in layer["children"]
            ]
            return layer
        
        if root_id:
            if root_id not in self.layers:
                return {}
            return build_tree(root_id)
        
        # Return all root layers with their trees
        roots = [
            layer_id for layer_id, layer in self.layers.items()
            if layer["parent_id"] is None
        ]
        
        return {
            "roots": [build_tree(root_id) for root_id in roots],
            "total_layers": len(self.layers)
        }
    
    def get_path(self, layer_id: str) -> List[Dict[str, Any]]:
        """
        Get the path from root to the specified layer
        
        Args:
            layer_id: The target layer
            
        Returns:
            List of layers from root to target
        """
        if layer_id not in self.layers:
            return []
        
        path = []
        current_id = layer_id
        
        while current_id:
            layer = self.layers[current_id]
            path.insert(0, {
                "id": layer["id"],
                "name": layer["name"],
                "description": layer["description"]
            })
            current_id = layer["parent_id"]
        
        return path
