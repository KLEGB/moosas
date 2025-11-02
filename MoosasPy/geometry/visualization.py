"""
Temporary visualization for transformation module
"""
from __future__ import annotations
from collections import Iterable

import numpy as np
import pygeos

from ..geometry.element import MoosasGeometry


# lagacy method for contourOld
def plot_plan_in_node(node_list, boundary_list, location_list, save=False, show=True):
    """
    Plot a plan in a node with given boundaries and locations.
    
    Parameters
    ----------
    node_list : list
        List of nodes to be plotted.
    boundary_list : list
        List of boundary coordinates defining the regions.
    location_list : list
        List of location coordinates to be marked on the plot.
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
        Plot a line between two points defined by indices in a location list.
        
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
        p1 = [pygeos.get_x(location_list[i]), pygeos.get_y(location_list[i])]
        p2 = [pygeos.get_x(location_list[j]), pygeos.get_y(location_list[j])]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color)

    def patch(boundary, color=None):
        """
        Create a filled polygon patch from boundary coordinates and optionally color it.
        
        Parameters
        ----------
        boundary : list of int
            List of indices referring to points in `location_list` that form the boundary of the polygon.
        color : array-like of float, optional
            RGB color triplet (e.g., [r, g, b]) used to fill the polygon. If provided, also annotates 
            the patch with the rounded red channel value at the centroid. Default is None, resulting in a fill without a specified color.
        
        Returns
        -------
        None
            This function does not return a value. It modifies the current matplotlib plot by adding a filled polygon and optionally a text annotation.
        """
        x = [pygeos.get_x(location_list[boundary[i]]) for i in range(len(boundary))]
        y = [pygeos.get_y(location_list[boundary[i]]) for i in range(len(boundary))]
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


def plot_object(*geoCollection, colors='black', show=True, filled=False):
    """
    Plot geometric objects using matplotlib.
    
    Parameters
    ----------
    geoCollection : iterable of array-like or pygeos.Geometry objects
        Variable number of geometric collections or individual geometries to plot.
        Each can be a pygeos geometry, an iterable of coordinates, or an object with a `force_2d` method.
    colors : str or list of str, optional
        Color(s) to use for plotting the geometries. If a single string is provided,
        it is applied to all collections. If a list, must have length matching `geoCollection`,
        otherwise the last color is repeated as needed. Default is 'black'.
    show : bool, optional
        If True, display the plot immediately. Default is True.
    filled : bool, optional
        If True, fill the interior of the plotted shapes. Default is False.
    
    Returns
    -------
    None
        This function does not return a value. It renders a plot using matplotlib.
    """
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    if isinstance(colors, str):
        colors = [colors]
    if len(colors) != len(geoCollection):
        for _ in range(len(geoCollection) - len(colors)):
            colors.append(colors[-1])
    for color, collection in zip(colors, geoCollection):
        if not isinstance(collection, Iterable):
            collection = [collection]
        plotCollection = []
        for figure in collection:

            if isinstance(figure, pygeos.Geometry):
                plotCollection.append(pygeos.get_coordinates(figure))
            elif isinstance(figure, Iterable):
                plotCollection.append(figure)
            elif hasattr(figure, 'force_2d'):
                if isinstance(figure.force_2d(),pygeos.Geometry):
                    plotCollection.append(pygeos.get_coordinates(figure.force_2d()))

        for fig in plotCollection:
            plt.plot(fig.T[0], fig.T[1], color=color)
            if filled:
                plt.fill(fig.T[0], fig.T[1], color=color)
    if show:
            plt.show(block=True)
