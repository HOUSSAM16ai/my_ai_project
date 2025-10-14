"""
Test Takbak Service - اختبار خدمة الطبقات
=========================================
Unit tests for the Takbak (layers) management service.

الغرض (Purpose):
اختبارات شاملة لخدمة إدارة الطبقات التنظيمية
"""

import pytest
from app.services.takbak_service import TakbakService


class TestTakbakService:
    """Test suite for TakbakService"""
    
    def setup_method(self):
        """Setup test fixtures before each test"""
        self.service = TakbakService()
    
    def test_create_layer(self):
        """Test creating a basic layer"""
        layer = self.service.create_layer(
            layer_id="layer1",
            name="Test Layer",
            description="A test layer"
        )
        
        assert layer["id"] == "layer1"
        assert layer["name"] == "Test Layer"
        assert layer["description"] == "A test layer"
        assert layer["parent_id"] is None
        assert "created_at" in layer
        assert layer["children"] == []
    
    def test_create_layer_with_parent(self):
        """Test creating a child layer"""
        # Create parent
        parent = self.service.create_layer(
            layer_id="parent",
            name="Parent Layer"
        )
        
        # Create child
        child = self.service.create_layer(
            layer_id="child",
            name="Child Layer",
            parent_id="parent"
        )
        
        assert child["parent_id"] == "parent"
        assert "child" in parent["children"]
    
    def test_create_duplicate_layer(self):
        """Test that creating duplicate layer raises error"""
        self.service.create_layer(layer_id="dup", name="Duplicate")
        
        with pytest.raises(ValueError, match="already exists"):
            self.service.create_layer(layer_id="dup", name="Duplicate 2")
    
    def test_create_layer_with_invalid_parent(self):
        """Test creating layer with non-existent parent"""
        with pytest.raises(ValueError, match="Parent layer .* not found"):
            self.service.create_layer(
                layer_id="orphan",
                name="Orphan",
                parent_id="nonexistent"
            )
    
    def test_get_layer(self):
        """Test retrieving a layer"""
        self.service.create_layer(layer_id="get_me", name="Get Me")
        
        layer = self.service.get_layer("get_me")
        assert layer is not None
        assert layer["id"] == "get_me"
        
        # Test non-existent layer
        assert self.service.get_layer("nonexistent") is None
    
    def test_list_all_layers(self):
        """Test listing all root layers"""
        self.service.create_layer(layer_id="root1", name="Root 1")
        self.service.create_layer(layer_id="root2", name="Root 2")
        self.service.create_layer(
            layer_id="child1",
            name="Child 1",
            parent_id="root1"
        )
        
        # List all root layers
        roots = self.service.list_layers()
        assert len(roots) == 2
        assert all(layer["parent_id"] is None for layer in roots)
    
    def test_list_layers_by_parent(self):
        """Test listing layers filtered by parent"""
        self.service.create_layer(layer_id="parent", name="Parent")
        self.service.create_layer(
            layer_id="child1",
            name="Child 1",
            parent_id="parent"
        )
        self.service.create_layer(
            layer_id="child2",
            name="Child 2",
            parent_id="parent"
        )
        
        children = self.service.list_layers(parent_id="parent")
        assert len(children) == 2
        assert all(layer["parent_id"] == "parent" for layer in children)
    
    def test_update_layer(self):
        """Test updating layer information"""
        self.service.create_layer(
            layer_id="update_me",
            name="Original Name",
            description="Original"
        )
        
        updated = self.service.update_layer(
            layer_id="update_me",
            name="New Name",
            description="Updated"
        )
        
        assert updated["name"] == "New Name"
        assert updated["description"] == "Updated"
        assert "updated_at" in updated
    
    def test_update_nonexistent_layer(self):
        """Test updating non-existent layer raises error"""
        with pytest.raises(ValueError, match="not found"):
            self.service.update_layer(
                layer_id="nonexistent",
                name="New Name"
            )
    
    def test_delete_layer(self):
        """Test deleting a layer"""
        self.service.create_layer(layer_id="delete_me", name="Delete Me")
        
        success = self.service.delete_layer("delete_me")
        assert success is True
        assert self.service.get_layer("delete_me") is None
        
        # Test deleting non-existent layer
        success = self.service.delete_layer("nonexistent")
        assert success is False
    
    def test_delete_layer_with_children_without_cascade(self):
        """Test that deleting parent with children requires cascade"""
        self.service.create_layer(layer_id="parent", name="Parent")
        self.service.create_layer(
            layer_id="child",
            name="Child",
            parent_id="parent"
        )
        
        with pytest.raises(ValueError, match="has children"):
            self.service.delete_layer("parent", cascade=False)
    
    def test_delete_layer_with_cascade(self):
        """Test deleting layer with children using cascade"""
        self.service.create_layer(layer_id="parent", name="Parent")
        self.service.create_layer(
            layer_id="child1",
            name="Child 1",
            parent_id="parent"
        )
        self.service.create_layer(
            layer_id="child2",
            name="Child 2",
            parent_id="parent"
        )
        
        success = self.service.delete_layer("parent", cascade=True)
        assert success is True
        assert self.service.get_layer("parent") is None
        assert self.service.get_layer("child1") is None
        assert self.service.get_layer("child2") is None
    
    def test_get_hierarchy(self):
        """Test getting complete hierarchy tree"""
        # Create hierarchy
        self.service.create_layer(layer_id="root", name="Root")
        self.service.create_layer(
            layer_id="level1",
            name="Level 1",
            parent_id="root"
        )
        self.service.create_layer(
            layer_id="level2",
            name="Level 2",
            parent_id="level1"
        )
        
        hierarchy = self.service.get_hierarchy()
        
        assert "roots" in hierarchy
        assert hierarchy["total_layers"] == 3
        assert len(hierarchy["roots"]) == 1
        
        # Check nested structure
        root = hierarchy["roots"][0]
        assert root["id"] == "root"
        assert len(root["children"]) == 1
        assert root["children"][0]["id"] == "level1"
        assert len(root["children"][0]["children"]) == 1
    
    def test_get_hierarchy_from_specific_root(self):
        """Test getting hierarchy from specific root"""
        self.service.create_layer(layer_id="root1", name="Root 1")
        self.service.create_layer(layer_id="root2", name="Root 2")
        self.service.create_layer(
            layer_id="child",
            name="Child",
            parent_id="root1"
        )
        
        hierarchy = self.service.get_hierarchy(root_id="root1")
        
        assert hierarchy["id"] == "root1"
        assert len(hierarchy["children"]) == 1
        assert hierarchy["children"][0]["id"] == "child"
    
    def test_get_path(self):
        """Test getting path from root to layer"""
        self.service.create_layer(layer_id="root", name="Root")
        self.service.create_layer(
            layer_id="middle",
            name="Middle",
            parent_id="root"
        )
        self.service.create_layer(
            layer_id="leaf",
            name="Leaf",
            parent_id="middle"
        )
        
        path = self.service.get_path("leaf")
        
        assert len(path) == 3
        assert path[0]["id"] == "root"
        assert path[1]["id"] == "middle"
        assert path[2]["id"] == "leaf"
    
    def test_get_path_for_root_layer(self):
        """Test getting path for root layer"""
        self.service.create_layer(layer_id="root", name="Root")
        
        path = self.service.get_path("root")
        
        assert len(path) == 1
        assert path[0]["id"] == "root"
    
    def test_get_path_for_nonexistent_layer(self):
        """Test getting path for non-existent layer"""
        path = self.service.get_path("nonexistent")
        assert path == []
    
    def test_layer_metadata(self):
        """Test storing and updating metadata"""
        layer = self.service.create_layer(
            layer_id="meta",
            name="Meta Layer",
            metadata={"key1": "value1", "key2": 123}
        )
        
        assert layer["metadata"]["key1"] == "value1"
        assert layer["metadata"]["key2"] == 123
        
        # Update metadata
        updated = self.service.update_layer(
            layer_id="meta",
            metadata={"key3": "value3"}
        )
        
        assert "key1" in updated["metadata"]
        assert "key3" in updated["metadata"]


class TestTakbakServiceEdgeCases:
    """Test edge cases and special scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = TakbakService()
    
    def test_multiple_root_layers(self):
        """Test handling multiple root layers"""
        for i in range(5):
            self.service.create_layer(
                layer_id=f"root{i}",
                name=f"Root {i}"
            )
        
        roots = self.service.list_layers()
        assert len(roots) == 5
    
    def test_deep_hierarchy(self):
        """Test deep nested hierarchy"""
        parent_id = None
        for i in range(10):
            layer = self.service.create_layer(
                layer_id=f"level{i}",
                name=f"Level {i}",
                parent_id=parent_id
            )
            parent_id = layer["id"]
        
        path = self.service.get_path("level9")
        assert len(path) == 10
    
    def test_list_layers_without_children_info(self):
        """Test listing layers without children information"""
        self.service.create_layer(layer_id="parent", name="Parent")
        self.service.create_layer(
            layer_id="child",
            name="Child",
            parent_id="parent"
        )
        
        layers = self.service.list_layers(include_children=False)
        
        assert len(layers) == 1
        assert "children" not in layers[0]
