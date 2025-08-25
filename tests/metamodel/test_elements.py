import pytest
import weakref
from typing import Type

from code_cartographer.metamodel.elements import (
    CodeUnit,
    PackageUnit,
    ModuleUnit,
    ClassifierUnit,
    MemberUnit,
)

# A fixture to provide instances of each CodeUnit subclass for repetitive tests
@pytest.fixture(params=[PackageUnit, ModuleUnit, ClassifierUnit, MemberUnit])
def code_unit_instance(request):
    unit_class: Type[CodeUnit] = request.param
    return unit_class("test_unit")

def test_code_unit_initialization(code_unit_instance: CodeUnit):
    """Tests that a CodeUnit is initialized with correct default values."""
    assert code_unit_instance.name == "test_unit"
    assert code_unit_instance.parent is None
    assert len(list(code_unit_instance.children)) == 0

def test_add_child():
    """Tests the correct establishment of the parent-child relationship."""
    parent = PackageUnit("parent")
    child = ModuleUnit("child")
    parent.add_child(child)

    assert child.parent is parent
    assert list(parent.children) == [child]
    assert parent.get_child("child") is child

def test_add_child_raises_error_on_duplicate_name():
    """Tests that adding a child with a duplicate name raises a ValueError."""
    parent = PackageUnit("parent")
    child1 = ModuleUnit("child1")
    child2_same_name = ModuleUnit("child1")
    parent.add_child(child1)

    with pytest.raises(ValueError, match="Child with name 'child1' already exists."):
        parent.add_child(child2_same_name)

def test_fqn_computation():
    """Tests the recursive computation of the fully-qualified name."""
    root = PackageUnit("my_project")
    services = PackageUnit("services")
    payment = ModuleUnit("payment")
    payment_service = ClassifierUnit("PaymentService")

    root.add_child(services)
    services.add_child(payment)
    payment.add_child(payment_service)

    assert root.fqn == "my_project"
    assert services.fqn == "my_project.services"
    assert payment.fqn == "my_project.services.payment"
    assert payment_service.fqn == "my_project.services.payment.PaymentService"

def test_parent_is_weak_reference():
    """Ensures the parent attribute is a weak reference to prevent memory leaks."""
    parent = PackageUnit("parent")
    child = ModuleUnit("child")
    parent.add_child(child)
    
    # The parent property should return the referenced object
    assert child.parent is parent
    
    # Check the internal storage to confirm it's a weakref
    # This is a white-box test, but important for this specific contract
    assert isinstance(child._parent_ref, weakref.ref)
    
    # When the parent is deleted, the weak reference should expire
    del parent
    assert child.parent is None

def test_classifier_unit_additional_attributes():
    """Tests the specific attributes of the ClassifierUnit."""
    classifier = ClassifierUnit("MyClass")
    classifier.base_classes = ["abc.ABC", "collections.UserDict"]
    classifier.is_abstract = True

    assert classifier.base_classes == ["abc.ABC", "collections.UserDict"]
    assert classifier.is_abstract is True
    # Test defaults
    assert ClassifierUnit("DefaultClass").base_classes == []
    assert ClassifierUnit("DefaultClass").is_abstract is False

def test_member_unit_additional_attributes():
    """Tests the specific attributes of the MemberUnit."""
    member = MemberUnit("my_method")
    member.visibility = "private"

    assert member.visibility == "private"
    # Test default
    assert MemberUnit("DefaultMember").visibility == "public"