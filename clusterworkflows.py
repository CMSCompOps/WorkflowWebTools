"""
Tools for clustering workflows based on their errors

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import sklearn.cluster


def get_clusterer():
    """
    Use this function to get the clusterer of workflows

    :return: A clusterer that is fitted to data.
    :rtype: sklearn.cluster
    """

    clusterer = sklearn.cluster.KMeans()

    return clusterer
