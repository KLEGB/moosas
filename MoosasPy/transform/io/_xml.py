from __future__ import annotations

from collections import defaultdict

from ._geo import _readGeo, preClassified
from ...models import *
from ...utils import ET, np


def _xml_float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_xml(model: MoosasModel, write_geometry: bool = False) -> ET.Element:
    """Build the XML representation of a complete Moosas model."""
    root = ET.Element("model")
    elements = {"MoosasFace": set(), "MoosasSkylight": set(), "MoosasWall": set(), "MoosasGlazing": set()}
    for space in model.spaceList + model.voidList:
        root.append(space.to_xml(model, writeGeometry=write_geometry))
        element_dict = space.getAllFaces(to_dict=True)
        elements["MoosasFace"] |= set(element_dict["MoosasFloor"] + element_dict["MoosasCeiling"])
        elements["MoosasWall"] |= set(element_dict["MoosasWall"] + element_dict["InternalMass"])
        elements["MoosasSkylight"] |= set(element_dict["MoosasSkylight"])
        elements["MoosasGlazing"] |= set(element_dict["MoosasGlazing"])

    for face in elements["MoosasFace"]:
        root.append(face.to_xml(model, writeGeometry=write_geometry))
    for wall in elements["MoosasWall"]:
        root.append(wall.to_xml(model, writeGeometry=write_geometry))
    for glazing in elements["MoosasGlazing"]:
        root.append(glazing.to_xml(model, writeGeometry=write_geometry))
    for skylight in elements["MoosasSkylight"]:
        root.append(skylight.to_xml(model, writeGeometry=write_geometry))

    shading = ET.SubElement(root, "shading")
    for glazing in model.glazingList:
        for shade in glazing.shading:
            face = ET.SubElement(shading, "face")
            face.text = str(shade)
            face.set("glazingId", str(glazing.faceId))
    ET.SubElement(root, "level").text = " ".join(np.array(model.levelList).astype(str))
    return root


def writeXml(file_path, model: MoosasModel, writeGeometry=False) -> ET.ElementTree:
    """Get a xml file describe the space topology.
        we have 3 different level of data:

        <face>
            <Uid> unique id, which is random generated. </Uid>
            <faceId> the faceId of the faces in the geo data or file. </faceId>
            <level> the faceId of the faces in the geo data or file. </level>
            <offset> the element's offset from the building level. </offset>
            <area> the total surface area. </area>
            <glazingId> glazing faceId in the geo data or file. </glazingId>
            <height> level + offset </height>
            <normal> element's normal, point to exterior. (x y z) </normal>
            <external> whether the element is connected to exterior. </external>
            <space> the space id which this element belongs to. </space>
        </face>

        <topology>
            <floor>
                <face>...</face>
            </floor>
            <ceiling>
                <face>...</face>
            </ceiling>
            <edge>
                <face>...</face>
            </edge>
        </topology>

        <space>
            <id>
                unique space id, which is calculated based on the shape & location of the space.
                It is the same in each we call transfrom()
            </id>
            <area> space area </area>
            <height> space height </height>
            <boundary> space 1 level space boundary (1LSB) {pt:[[x,y,z]...]}
                <pt>216.53 393.70 0.0</pt>
                <pt>... ... ...</pt>
                <pt>216.53 177.16 0.0</pt>
            </boundary>

            <internal_wall> the internalMass in the space
                <face>...</face>
            </internal_wall>
            <topology>
                <floor>...</floor>
                <ceiling>...</ceiling>
                <edge>...</edge>
            </topology>
            <neighbor> the neighborhood space share the same 2 level space boundary (2LSB)
                <faceId> the faceId of the 2LSB in the geo file, </faceId>
                <id> the neighbor space id </id>
            </neighbor>
            <setting> thermal settings of the space in dictionary, defined by transformation.io.idf.model
                ...
            </setting>
            <void> the void inside the space, also formatted in space[{space}..]
                ...
            </void>
        </space>

        Args:
            file_path(str): output space xml file path
            model(MoosasModel): model to export
            writeGeometry(bool): whether write geometry in the file

        Returns:
            ElementTree
        """
    path.checkBuildDir(file_path)
    tree = ET.ElementTree(build_xml(model, writeGeometry))
    tree.write(file_path)

    return tree


def loadXml(filePath, geoPath):
    # initialize model
    model: MoosasModel = MoosasModel()
    model.geometryList = _readGeo(geoPath)
    model = preClassified(model)
    # read the tree to dict
    root = praseXml(filePath)['model']

    # construct LevelList
    level = set()
    for i, element in enumerate(root['face']):
        print(f'\rLOADING: find level {i + 1}/{len(root["face"])}', end='')
        level.add(float(element['level']))
    model.levelList = list(level)
    model.levelList.sort()
    print()

    # construct MoosasFaceList
    for i, element in enumerate(root['face']):
        faceInfo = element
        Uid = str(element['Uid'])
        u_value = _xml_float_or_none(faceInfo.get('U_Value'))
        existing = searchBy('Uid', Uid, model.faceList, earlyEnd=True, asObject=True)
        if existing:
            if u_value is not None:
                existing[0].U_Value = u_value
            continue
        offset = float(element['offset'])
        level = float(element['level'])
        geoId = mixItemListToObject(element['faceId'].split(' '))
        element = MoosasFace(model, geoId, level=level, uid=Uid, offset=offset)
        if u_value is not None:
            element.U_Value = u_value
        model.faceList.append(element)
        print(f'\rLOADING: Faces {i + 1}/{len(root["face"])}', end='')
    print()
    # construct MoosasWallList
    for i, element in enumerate(root['wall']):
        wallInfo = element
        Uid = str(element['Uid'])
        u_value = _xml_float_or_none(wallInfo.get('U_Value'))
        existing = searchBy('Uid', Uid, model.wallList, earlyEnd=True, asObject=True)
        if existing:
            if u_value is not None:
                existing[0].U_Value = u_value
            continue
        offset = float(element['offset'])
        level = float(element['level'])
        geoId = mixItemListToObject(element['faceId'].split(' '))
        element = MoosasWall(model, geoId, level=level, uid=Uid, offset=offset)
        if u_value is not None:
            element.U_Value = u_value
        model.wallList.append(element)
        print(f'\rLOADING: Faces {i + 1}/{len(root["wall"])}', end='')
    print()
    # construct MoosasGlazingList
    if "glazing" in root:
        for i, element in enumerate(root['glazing']):
            glazingInfo = element
            Uid = str(element['Uid'])
            u_value = _xml_float_or_none(glazingInfo.get('U_Value'))
            shgc = _xml_float_or_none(glazingInfo.get('SHGC'))
            existing = searchBy('Uid', Uid, model.glazingList, earlyEnd=True, asObject=True)
            if existing:
                if u_value is not None:
                    existing[0].U_Value = u_value
                if shgc is not None:
                    existing[0].SHGC = shgc
                continue
            offset = float(element['offset'])
            level = float(element['level'])
            geoId = mixItemListToObject(element['faceId'].split(' '))
            element = MoosasGlazing(model, geoId, level=level, uid=Uid, offset=offset)
            if u_value is not None:
                element.U_Value = u_value
            if shgc is not None:
                element.SHGC = shgc
            model.glazingList.append(element)
            print(f'\rLOADING: Faces {i + 1}/{len(root["glazing"])}', end='')
        print()
    # construct MoosasSkylightList
    if "skylight" in root:
        for i, element in enumerate(root['skylight']):
            skylightInfo = element
            Uid = str(element['Uid'])
            u_value = _xml_float_or_none(skylightInfo.get('U_Value'))
            shgc = _xml_float_or_none(skylightInfo.get('SHGC'))
            existing = searchBy('Uid', Uid, model.skylightList, earlyEnd=True, asObject=True)
            if existing:
                if u_value is not None:
                    existing[0].U_Value = u_value
                if shgc is not None:
                    existing[0].SHGC = shgc
                continue
            offset = float(element['offset'])
            level = float(element['level'])
            geoId = mixItemListToObject(element['faceId'].split(' '))
            element = MoosasSkylight(model, geoId, level=level, uid=Uid, offset=offset)
            if u_value is not None:
                element.U_Value = u_value
            if shgc is not None:
                element.SHGC = shgc
            model.skylightList.append(element)
            print(f'\rLOADING: Faces {i + 1}/{len(root["skylight"])}', end='')
        print()
    # load space
    for i, element in enumerate(root['space']):
        topology = {"Floor": None, "ceiling": None, "Edge": None}
        if "floor" in element['topology']:
            element['topology']['floor']['face'] = mixItemListToList(element['topology']['floor']['face'])
            floors = [searchBy('Uid', face, model.faceList, earlyEnd=True, asObject=True)[0] for face in
                      element['topology']['floor']['face']]
            topology["Floor"] = MoosasFloor(floors)
        if "ceiling" in element['topology']:
            element['topology']['ceiling']['face'] = mixItemListToList(element['topology']['ceiling']['face'])
            ceilings = [searchBy('Uid', face, model.faceList, earlyEnd=True, asObject=True)[0] for face in
                        element['topology']['ceiling']['face']]
            topology["ceiling"] = MoosasFloor(ceilings)
        if "edge" in element['topology']:
            walls = [searchBy('Uid', face['Uid'], model.wallList, earlyEnd=True, asObject=True)[0] for face
                     in element['topology']['edge']['wall']]
            topology["Edge"] = MoosasEdge(walls)
        if topology["Edge"] is not None:
            Uid = str(element.get('id', None))
            spc = MoosasSpace(_floor=topology["Floor"], _ceiling=topology["ceiling"], _edge=topology["Edge"], Uid=Uid)

            for key in element['setting']:
                try:
                    spc.settings[key] = float(element['setting'][key])
                except ValueError:
                    spc.settings[key] = element['setting'][key]
            if spc.is_void():
                model.voidList.append(spc)
            else:
                model.spaceList.append(spc)
        print(f'\rLOADING: space {i + 1}/{len(root["space"])}', end='')
    print()
    return model


def praseXml(xml_path: str) -> dict:
    """
    Convert an XML file (with text-only nodes, no attributes, nested/repeated tags) to a simplified dictionary.

    Key features:
    - Nested nodes 鈫?nested dictionaries
    - Repeated nodes with the same tag 鈫?lists
    - Node text content 鈫?direct values (no special keys like #text/@attributes)
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

        # Case 1: No child nodes 鈫?return text directly (empty string for blank text)
        if not children:
            return text if text is not None else ""

        # Case 2: Has child nodes 鈫?process recursively
        child_groups = defaultdict(list)
        for child in children:
            child_groups[child.tag].append(_element_to_dict(child))

        # Build result dict (single child 鈫?value, multiple children 鈫?list)
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
