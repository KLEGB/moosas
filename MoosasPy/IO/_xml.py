
from ..utils import ET
from ..utils import path
def writeXml(file_path, model, writeGeometry=False) -> ET.ElementTree:
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
            <setting> thermal settings of the space in dictionary, you can find their names in .thermal.settings
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
    tree = ET.ElementTree(model.buildXml(writeGeometry))
    tree.write(file_path)

    return tree