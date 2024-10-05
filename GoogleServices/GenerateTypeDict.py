import json
from typing import Any, Dict

# Map JSON schema types to Python types
TYPE_MAPPING = {
    "string": "str",
    "boolean": "bool",
    "integer": "int",
    "number": "float",
    "array": "List",
    "object": "Dict",
}


# Function to handle individual property types
def convert_property_type(prop: Dict[str, Any]) -> str:
    if "$ref" in prop:
        # Handle references to other types, wrap in quotes for forward reference
        return f'"{prop["$ref"]}"'
    elif prop["type"] == "array":
        # Handle arrays
        items_type = convert_property_type(prop["items"])
        return f"List[{items_type}]"
    elif prop["type"] == "object":
        # Handle objects (nested types)
        return "Dict[str, Any]"
    else:
        # Convert basic types
        return TYPE_MAPPING.get(prop["type"], "Any")


# Function to generate TypedDict for each object
def generate_typeddict(name: str, obj: Dict[str, Any]) -> str:
    typeddict_lines = [f"class {name}(TypedDict, total=False):"]

    properties = obj.get("properties", {})
    if not properties:
        typeddict_lines.append("    pass")  # Add 'pass' if no properties exist
    else:
        for prop_name, prop_info in properties.items():
            py_type = convert_property_type(prop_info)
            typeddict_lines.append(f"    {prop_name}: {py_type}")

    return "\n".join(typeddict_lines)


# Main function to process the JSON schema
def convert_json_to_typeddict(json_schema: Dict[str, Any]) -> str:
    output = ["from typing import TypedDict, List, Dict, Any\n"]

    for obj_name, obj_info in json_schema.items():
        if obj_info.get("type") == "object":
            typeddict_definition = generate_typeddict(obj_name, obj_info)
            output.append(typeddict_definition + "\n")

    return "\n".join(output)


if __name__ == "__main__":
    # Read the schema JSON file
    with open("forms.json", "r") as f:
        forms = json.load(f)

    schema = forms.get("schemas", {})

    # Convert the JSON schema to TypedDicts
    typedict_code = convert_json_to_typeddict(schema)

    # Output the generated code
    with open("schemas.py", "w+") as f_out:
        f_out.write(typedict_code)
    print("TypedDict code has been written to schemas.py")

    # TODO: I would like to generate Classes with only types for the resources( Just to use for type hinting)
    # resources = forms.get("resources", {})
    # classes_code = convert_json_to_classes(resources)
    # with open("resources.py", "w+") as f_out:
    #     f_out.write(classes_code)
    # print("TypedDict code has been written to resources.py")
