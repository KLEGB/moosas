from .element import MoosasContainer, MoosasEdge
from .contour import closed_contour_calculation
from .viewFactor import viewFactorTopology
from ..utils import np, searchBy, pygeos
from .contour import _documentBoundary


def BTGSpaceGeneration(model: MoosasContainer) -> MoosasContainer:
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
    for bld_level in model.levelList:
        # wallList = np.array(model.wallList)[searchBy("level", bld_level, model.wallList)]
        # from .visual.geometry import plot_object
        # plot_object(wallList)
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


