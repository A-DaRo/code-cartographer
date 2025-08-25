from dataclasses import is_dataclass
import pytest

from code_cartographer.metamodel.relationship import Relationship, RelationshipType

def test_relationship_type_enum():
    """Tests that RelationshipType has the correct members."""
    assert RelationshipType.INHERITANCE.name == "INHERITANCE"
    assert RelationshipType.COMPOSITION.name == "COMPOSITION"
    assert RelationshipType.AGGREGATION.name == "AGGREGATION"
    assert RelationshipType.ASSOCIATION.name == "ASSOCIATION"
    assert RelationshipType.DEPENDENCY.name == "DEPENDENCY"

def test_relationship_is_immutable_dataclass():
    """Tests that the Relationship class is a dataclass and is frozen."""
    assert is_dataclass(Relationship)
    assert Relationship.__dataclass_params__.frozen is True

def test_relationship_creation():
    """Tests the creation of a Relationship object."""
    rel = Relationship(
        source_fqn="a.b.ClassA",
        target_fqn="c.d.ClassB",
        type=RelationshipType.ASSOCIATION,
        metadata={"label": "uses"}
    )
    assert rel.source_fqn == "a.b.ClassA"
    assert rel.target_fqn == "c.d.ClassB"
    assert rel.type == RelationshipType.ASSOCIATION
    assert rel.metadata == {"label": "uses"}

def test_relationship_immutability():
    """Ensures that attributes of a Relationship cannot be changed after creation."""
    rel = Relationship("a.b.A", "c.d.B", RelationshipType.INHERITANCE)
    with pytest.raises(AttributeError):
        rel.source_fqn = "x.y.Z"