from .element import MoosasContainer, MoosasEdge
from .contour import closed_contour_calculation
from .viewFactor import viewFactorTopology
from ...utils import np, searchBy, shapely
from .contour import _documentBoundary


def BTGSpaceGeneration(model: MoosasContainer) -> MoosasContainer:
    """
    Generate boundary space from model elements grouped by level.
    
    Parameters
    ----------
    model : MoosasContainer
        The container object holding building levels, faces, walls, and to which generated boundaries will be assigned.
    
    Returns
    -------
    MoosasContainer
        The input model with updated boundaryList containing walls identified as valid boundaries for each level.
    """
    validBound = []
    for bld_level in model.levelList:
        faceList = searchBy('level', bld_level, model.faceList, asObject=True)
        wallList = list(searchBy('level', bld_level, model.wallList, asObject=True))
        if len(wallList) > 0:
            for f in faceList:
                validBound.append(MoosasEdge.selectWall(f.force_2d(), wallList))
    model.boundaryList = [edge.wall for edge in validBound]
    return model


def CCRSpaceGeneration(model: MoosasContainer) -> MoosasContainer:
    """
    Perform closed contour calculation for each building level in the model.
    
    Parameters
    ----------
    model : MoosasContainer
        The input model container containing building levels and associated data.
        This object is updated in place with closed contour calculations.
    
    Returns
    -------
    MoosasContainer
        The updated model container after applying closed contour calculations for each level.
    """
    for bld_level in model.levelList:
        # wallList = np.array(model.wallList)[searchBy("level", bld_level, model.wallList)]
        model = closed_contour_calculation(model, bld_level)
    return model


def VFGSpaceGeneration(model: MoosasContainer) -> MoosasContainer:
    """calculate view factor to get the topology of the walls"""
    boundaries = []
    for bld_level in model.levelList:
        elementList = searchBy('level', bld_level, model.wallList, asObject=True)
        # elementList = list(model.wallList) + list(model.faceList)
        boundariesNew = viewFactorTopology(model,elementList,vfNumber=12)
        print(f'\rTOPOLOGY: in {bld_level}: find {len(boundariesNew)} boundaries')
        boundaries += boundariesNew
    return _documentBoundary(boundaries,model)


