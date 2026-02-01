from app.services.procedural_knowledge.domain import KnowledgeNode, NodeType, ProceduralGraph


def test_knowledge_node_hash():
    """Test that KnowledgeNode is hashable."""
    node1 = KnowledgeNode(id="n1", type=NodeType.ENTITY, label="Node 1")
    node2 = KnowledgeNode(id="n1", type=NodeType.ENTITY, label="Node 1")
    node3 = KnowledgeNode(id="n2", type=NodeType.ENTITY, label="Node 2")

    # Same ID should have same hash
    assert hash(node1) == hash(node2)
    # Different ID should have different hash (usually)
    assert hash(node1) != hash(node3)

    # Test usability in set
    s = {node1, node3}
    assert len(s) == 2
    s.add(node2)  # Should be duplicate if hashing works on ID
    assert len(s) == 2


def test_procedural_graph_get_node():
    """Test retrieving nodes from the graph."""
    graph = ProceduralGraph()
    node = KnowledgeNode(id="n1", type=NodeType.ENTITY, label="Node 1")
    graph.add_node(node)

    # Test success
    retrieved = graph.get_node("n1")
    assert retrieved == node

    # Test not found
    assert graph.get_node("missing") is None
