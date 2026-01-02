from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
import json


def read_xml_to_simple_dict(xml_path: str) -> dict:
    """
    Convert an XML file (with text-only nodes, no attributes, nested/repeated tags) to a simplified dictionary.

    Key features:
    - Nested nodes → nested dictionaries
    - Repeated nodes with the same tag → lists
    - Node text content → direct values (no special keys like #text/@attributes)
    - No attribute handling (optimized for attribute-free XML)

    Parameters
    ----------
    xml_path : str
        File path to the target XML file (absolute/relative path)

    Returns
    -------
    dict
        Simplified nested dictionary with:
        - Root tag as the top-level key
        - Repeated child nodes stored as lists
        - Nested child nodes stored as sub-dictionaries
        - Text content as direct values of corresponding keys

    Raises
    ------
    FileNotFoundError
        If the specified XML file does not exist at the given path
    ET.ParseError
        If the XML file has invalid syntax or cannot be parsed
    ValueError
        Wrapper for XML parsing errors with human-readable messages

    Examples
    --------
    Sample XML content (test_simple.xml):
    <?xml version="1.0" encoding="UTF-8"?>
    <root>
        <person>
            <name>Zhang San</name>
            <age>25</age>
            <address>
                <city>Beijing</city>
                <district>Haidian</district>
            </address>
            <hobby>Coding</hobby>
            <hobby>Reading</hobby>
        </person>
        <person>
            <name>Li Si</name>
            <age>30</age>
        </person>
        <remark>Test data for XML conversion</remark>
    </root>

    Usage:
    >>> result = read_xml_to_simple_dict("test_simple.xml")
    >>> print(json.dumps(result, ensure_ascii=False, indent=2))
    {
      "root": {
        "person": [
          {
            "name": "Zhang San",
            "age": "25",
            "address": {"city": "Beijing", "district": "Haidian"},
            "hobby": ["Coding", "Reading"]
          },
          {
            "name": "Li Si",
            "age": "30"
          }
        ],
        "remark": "Test data for XML conversion"
      }
    }
    """

    # Internal recursive function to process XML elements
    def _element_to_dict(element: ET.Element) -> dict | list | str:
        """
        Recursively convert an ElementTree Element to a dictionary/list/text value.

        Parameters
        ----------
        element : ET.Element
            Single XML element node to process

        Returns
        -------
        dict | list | str
            Converted value (dict for nested nodes, list for repeated nodes, str for text)
        """
        # Clean up text content (remove leading/trailing whitespace)
        text = element.text.strip() if element.text else None

        # Get child nodes list
        children = list(element)

        # Case 1: No child nodes → return text directly (empty string for blank text)
        if not children:
            return text if text is not None else ""

        # Case 2: Has child nodes → process recursively
        child_groups = defaultdict(list)
        for child in children:
            child_groups[child.tag].append(_element_to_dict(child))

        # Build result dict (single child → value, multiple children → list)
        result = {}
        for tag, child_values in child_groups.items():
            if len(child_values) == 1:
                result[tag] = child_values[0]
            else:
                result[tag] = child_values

        # Rare case: Element has both children and text content
        if text:
            result["_text"] = text

        return result

    # Main logic: Parse XML file and convert to dict
    try:
        # Parse XML file and get root element
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Convert root element to dict and return
        return {root.tag: _element_to_dict(root)}

    except FileNotFoundError as e:
        raise FileNotFoundError(f"XML file not found at path: {xml_path}") from e
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML file (invalid syntax): {str(e)}") from e


# ------------------------------ Test Code ------------------------------
if __name__ == "__main__":
    xml_dict_result = read_xml_to_simple_dict(r'\\166.111.40.8\protect\moosasTestModelDataset\SRT_DATA\new_xml\cyh_25_01102_01102-01.xml')
    print(xml_dict_result)