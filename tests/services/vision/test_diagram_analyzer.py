from app.services.vision.diagram_analyzer import (
    DiagramAnalyzer,
    DiagramType,
    get_diagram_analyzer,
)


def test_singleton_instance():
    analyzer1 = get_diagram_analyzer()
    analyzer2 = get_diagram_analyzer()
    assert analyzer1 is analyzer2
    assert isinstance(analyzer1, DiagramAnalyzer)


def test_classify_function_graph():
    analyzer = DiagramAnalyzer()
    desc = "This is a function graph showing a parabola."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.FUNCTION_GRAPH
    assert analysis.description == desc


def test_classify_probability_tree():
    analyzer = DiagramAnalyzer()
    desc = "A probability tree diagram showing coin flips."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.PROBABILITY_TREE
    assert "شجرة احتمالات" in analysis.elements


def test_classify_venn_diagram():
    analyzer = DiagramAnalyzer()
    desc = "A venn diagram showing intersection of sets A and B."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.VENN_DIAGRAM


def test_classify_geometric_shape():
    analyzer = DiagramAnalyzer()
    desc = "A geometric shape: a triangle with 90 degree angle."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.GEOMETRIC_SHAPE
    assert "numbers" in analysis.mathematical_info
    assert 90.0 in analysis.mathematical_info["numbers"]


def test_classify_complex_plane():
    analyzer = DiagramAnalyzer()
    desc = "Plot on the complex plane with imaginary axis."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.COMPLEX_PLANE


def test_classify_table():
    analyzer = DiagramAnalyzer()
    desc = "A data table with rows and columns."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.TABLE


def test_classify_unknown():
    analyzer = DiagramAnalyzer()
    desc = "Just a random drawing of a cat."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.UNKNOWN


def test_extract_elements_function_points():
    analyzer = DiagramAnalyzer()
    desc = "Function graph passing through points (0,1) and (2,3)."
    analysis = analyzer.analyze_from_description(desc)
    assert analysis.diagram_type == DiagramType.FUNCTION_GRAPH
    assert any("0,1" in e for e in analysis.elements)
    assert any("2,3" in e for e in analysis.elements)


def test_extract_math_info_numbers():
    analyzer = DiagramAnalyzer()
    desc = "A shape with side length 5.5 and area 20."
    analysis = analyzer.analyze_from_description(desc)
    assert "numbers" in analysis.mathematical_info
    assert 5.5 in analysis.mathematical_info["numbers"]
    assert 20.0 in analysis.mathematical_info["numbers"]


def test_describe_for_ai():
    analyzer = DiagramAnalyzer()
    desc = "Function graph with point (1,1)"
    analysis = analyzer.analyze_from_description(desc)
    ai_desc = analyzer.describe_for_ai(analysis)
    assert "نوع الرسم: function_graph" in ai_desc
    assert "الوصف: Function graph with point (1,1)" in ai_desc
    assert "العناصر:" in ai_desc
    assert "معلومات رياضية:" in ai_desc
