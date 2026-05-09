"""
Temporary visualization for transformation module
"""
from __future__ import annotations
from ..utils import Iterable
import numpy as np
import shapely



# lagacy method for contourOld
def plot_plan_in_node(node_list, boundary_list, location_list, save=False, show=True):
    """
    Plot a plan in a node with given node, boundary, and location lists.
    
    Parameters
    ----------
    node_list : list
        List of nodes to be plotted.
    boundary_list : list
        List of boundaries to be plotted.
    location_list : list
        List of locations to be plotted.
    save : bool, optional
        If True, saves the plot to a file. Default is False.
    show : bool, optional
        If True, displays the plot. Default is True.
    
    Returns
    -------
    myfig : matplotlib.figure.Figure
        The current figure object containing the plot.
    """
    import os
    import matplotlib.pyplot as plt
    myfig = plt.gcf()

    def plot(i, j, color='black'):
        """
        Plot a line segment between two points from a location list.
        
        Parameters
        ----------
        i : int
            Index of the first point in the location_list.
        j : int
            Index of the second point in the location_list.
        color : str, optional
            Color of the line to be plotted. Default is 'black'.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the current matplotlib plot.
        """
        p1 = [shapely.get_x(location_list[i]), shapely.get_y(location_list[i])]
        p2 = [shapely.get_x(location_list[j]), shapely.get_y(location_list[j])]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color)

    def patch(boundary, color=None):
        """
        Create a filled polygon patch from a boundary and optionally color it.
        
        Parameters
        ----------
        boundary : list of int
            List of indices representing the boundary vertices.
        color : array-like of shape (3,), optional
            RGB color tuple to fill the patch. If not provided, defaults to no fill color.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the current matplotlib plot.
        """
        x = [shapely.get_x(location_list[boundary[i]]) for i in range(len(boundary))]
        y = [shapely.get_y(location_list[boundary[i]]) for i in range(len(boundary))]
        if color:
            plt.fill(x, y, color=color)
            plt.text(np.mean(x), np.mean(y), f'{np.round(color[0], 2)}')
        else:
            plt.fill(x, y)

    for i in range(len(node_list)):
        for j in node_list[i]:
            plot(i, j)
    for bound in boundary_list:
        for i in range(1, len(bound)):
            plot(bound[i - 1], bound[i], 'red')
        color_arg = boundary_list.index(bound) / len(boundary_list)
        patch(bound, color=[color_arg, color_arg, 1 - color_arg])
    if save:
        i = len(os.listdir('./figure/'))
        myfig.savefig('./figure/figure' + str(i) + '.png')
    if show:
        plt.show(block=True)


def plot_object(*geoCollection, colors='black', lineSize=1, lineType='-', show=True, filled=False):
    """
    Plot geometric objects using matplotlib.
    
    Parameters
    ----------
    geoCollection : iterable of array-like or shapely.Geometry
        One or more geometric objects to plot. Each can be a Shapely geometry, 
        an iterable of coordinates, or an object with a `force_2d` method.
    colors : str or list of str, optional
        Color(s) for the plotted lines. If a single string is provided, it will be 
        applied to all geometries. If a list, must match the number of geoCollection 
        elements or be extended cyclically. Default is 'black'.
    lineSize : int or list of int, optional
        Line width(s) for the plotted lines. If a single integer is provided, 
        it will be applied to all geometries. If a list, must match the number 
        of geoCollection elements or be extended cyclically. Default is 1.
    lineType : str or list of str, optional
        Line style(s) (e.g., '-', '--', ':') for the plotted lines. If a single 
        string is provided, it will be applied to all geometries. If a list, 
        must match the number of geoCollection elements or be extended cyclically. 
        Default is '-'.
    show : bool, optional
        Whether to display the plot immediately. Default is True.
    filled : bool, optional
        Whether to fill the interior of the shapes. Default is False.
    
    Returns
    -------
    None
        This function does not return any value. It renders a plot using matplotlib.
    """
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    if isinstance(colors, str):
        colors = [colors]
    if isinstance(lineSize, int):
        lineSize = [lineSize]
    if isinstance(lineType, str):
        lineType = [lineType]
    if len(colors) != len(geoCollection):
        for _ in range(len(geoCollection) - len(colors)):
            colors.append(colors[-1])
    if len(lineSize) != len(geoCollection):
        for _ in range(len(geoCollection) - len(lineSize)):
            lineSize.append(lineSize[-1])
    if len(lineType) != len(geoCollection):
        for _ in range(len(geoCollection) - len(lineType)):
            lineType.append(lineType[-1])
    for color, collection, size, ltype in zip(colors, geoCollection, lineSize, lineType):
        if not isinstance(collection, Iterable):
            collection = [collection]
        plotCollection = []
        for figure in collection:

            if isinstance(figure, shapely.Geometry):
                plotCollection.append(shapely.get_coordinates(figure))
            elif isinstance(figure, Iterable):
                plotCollection.append(figure)
            elif hasattr(figure, 'force_2d'):
                if isinstance(figure.force_2d(), shapely.Geometry):
                    plotCollection.append(shapely.get_coordinates(figure.force_2d()))

        for fig in plotCollection:
            plt.plot(fig.T[0], fig.T[1], color=color, linewidth=size, linestyle=ltype)
            if filled:
                plt.fill(fig.T[0], fig.T[1], color=color, linewidth=size, linestyle=ltype)
    if show:
        plt.show(block=True)
