import pytest

from app.services.data_mesh.application.mesh_manager import DataMeshManager


def test_register_product_success():
    mesh_manager = DataMeshManager()

    product_def = {
        "product_id": "prod-1",
        "name": "User Product",
        "domain": "user_management",
        "description": "User data",
    }

    product = mesh_manager.register_product(product_def, "team-a")

    assert product.product_id == "prod-1"
    assert product.owner_team == "team-a"
    assert "prod-1" in mesh_manager.data_products


def test_register_product_missing_owner():
    mesh_manager = DataMeshManager()

    product_def = {"product_id": "prod-1", "name": "User Product", "domain": "user_management"}

    with pytest.raises(ValueError, match="Owner ID is required"):
        mesh_manager.register_product(product_def, "")


def test_register_product_duplicate():
    mesh_manager = DataMeshManager()

    product_def = {"product_id": "prod-1", "name": "User Product", "domain": "user_management"}

    mesh_manager.register_product(product_def, "team-a")

    with pytest.raises(ValueError, match="Product prod-1 already exists"):
        mesh_manager.register_product(product_def, "team-b")
