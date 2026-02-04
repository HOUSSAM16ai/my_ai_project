"""
Standalone verification script for Polymorphic Discriminator Resolution.
Bypasses the heavy pytest configuration to ensure quick feedback.
"""

import json
import sys

from pydantic import ValidationError

from app.core.polymorphism import Cat, Dog, PetOwner


def verify_polymorphic_deserialization():
    print("Testing Polymorphic Deserialization...", end=" ")
    data = {
        "owner_name": "Jules",
        "pets": [
            {"type": "dog", "name": "Buddy", "bark": True},
            {"type": "cat", "name": "Whiskers", "meow": True},
            {"type": "dog", "name": "Rex", "bark": False},
        ],
    }

    owner = PetOwner(**data)

    assert len(owner.pets) == 3
    assert isinstance(owner.pets[0], Dog)
    assert owner.pets[0].name == "Buddy"
    assert owner.pets[0].bark is True

    assert isinstance(owner.pets[1], Cat)
    assert owner.pets[1].name == "Whiskers"
    assert owner.pets[1].meow is True

    assert isinstance(owner.pets[2], Dog)
    assert owner.pets[2].name == "Rex"
    assert owner.pets[2].bark is False
    print("✅ Passed")


def verify_invalid_discriminator():
    print("Testing Invalid Discriminator...", end=" ")
    data = {
        "owner_name": "ErrorUser",
        "pets": [
            {"type": "bird", "name": "Tweety"}  # bird is not defined
        ],
    }

    try:
        PetOwner(**data)
        print("❌ Failed (Should have raised ValidationError)")
        sys.exit(1)
    except ValidationError as e:
        # Check that the error mentions the expected types
        error_str = str(e)
        if "dog" in error_str or "cat" in error_str or "Input should be" in error_str:
            print("✅ Passed")
        else:
            print(f"❌ Failed (Unexpected error message: {error_str})")
            sys.exit(1)


def verify_json_schema_generation():
    print("Testing JSON Schema Generation...", end=" ")
    schema = PetOwner.model_json_schema()

    # Navigate to the definition of the union
    defs = schema.get("$defs", {})

    # We look for the schema that uses discriminator.
    # Since PetUnion is an Annotated Union, it might be inlined or referenced.
    # In Pydantic V2, the property 'pets' items will point to it.

    pets_items = schema["properties"]["pets"]["items"]

    target_schema = None
    if "$ref" in pets_items:
        ref_name = pets_items["$ref"].split("/")[-1]
        target_schema = defs[ref_name]
    else:
        target_schema = pets_items

    # Check for 'discriminator' keyword
    if "discriminator" in target_schema:
        disc = target_schema["discriminator"]
        if isinstance(disc, dict) and disc.get("propertyName") == "type":
            print("✅ Passed")
            return

    # Fallback check: sometimes it's nested differently depending on Pydantic version nuances
    # Let's print the schema if we fail
    print(f"❌ Failed. Schema snippet: {json.dumps(target_schema, indent=2)}")
    sys.exit(1)


if __name__ == "__main__":
    print("Starting Standalone Verification for Polymorphism Solution")
    print("========================================================")
    verify_polymorphic_deserialization()
    verify_invalid_discriminator()
    verify_json_schema_generation()
    print("========================================================")
    print("All tests passed successfully.")
