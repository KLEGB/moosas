"""
Temporary visualization for transformation module
"""
from __future__ import annotations
from ..utils import Iterable
import numpy as np
import pygeos



# lagacy method for contourOld
def plot_plan_in_node(node_list, boundary_list, location_list, save=False, show=True):
    import os
    import matplotlib.pyplot as plt
    myfig = plt.gcf()

    def plot(i, j, color='black'):
        p1 = [pygeos.get_x(location_list[i]), pygeos.get_y(location_list[i])]
        p2 = [pygeos.get_x(location_list[j]), pygeos.get_y(location_list[j])]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color)

    def patch(boundary, color=None):
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


def plot_object(*geoCollection, colors='black', lineSize=1, lineType='-', show=True, filled=False):
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

            if isinstance(figure, pygeos.Geometry):
                plotCollection.append(pygeos.get_coordinates(figure))
            elif isinstance(figure, Iterable):
                plotCollection.append(figure)
            elif hasattr(figure, 'force_2d'):
                if isinstance(figure.force_2d(), pygeos.Geometry):
                    plotCollection.append(pygeos.get_coordinates(figure.force_2d()))

        for fig in plotCollection:
            plt.plot(fig.T[0], fig.T[1], color=color, linewidth=size, linestyle=ltype)
            if filled:
                plt.fill(fig.T[0], fig.T[1], color=color, linewidth=size, linestyle=ltype)
    if show:
        plt.show(block=True)
