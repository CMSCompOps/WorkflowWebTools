"""
This module uses neural net classifiers and regession to predict parameters
for error handling workflows.

.. Note::

   Regression part is a work in progress. Need more data.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sys
import json

from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from matplotlib import pyplot
from matplotlib.markers import MarkerStyle

def get_classifier(raw_data, parameter, **kwargs):
    """
    Fit a classifier.

    .. Note::

       Doesn't return anything useful at the moment. In development.

    :param dict raw_data: Raw data in the form of output from
                          :py:func:`actionshistorylink.dump_json`.
    :param str parameter: The parameter to classify.
    :param kwargs: These are kwargs for the ``sklearn.neural_network.MLPClassifier``
                   that is running underneath.
    """

    primary_ids = sorted(set([key.split('/')[1] for key in raw_data.keys()]))

    training_ids = primary_ids[0::2]

    training_data = []
    training_target = []
    testing_data = []
    testing_target = []

    class_labels = []

    # Prepare the data
    for key in sorted(raw_data):
        if key.split('/')[1] in training_ids:
            data = training_data
            target = training_target
        else:
            data = testing_data
            target = testing_target

        errors = raw_data[key]['errors']

        data.append(sum(errors['good_sites'] + errors['bad_sites'], []))

        param = raw_data[key]['parameters'].get(parameter, '')
        if param in class_labels:
            target.append(class_labels.index(param))
        else:
            target.append(len(class_labels))
            class_labels.append(param)

    classifier = MLPClassifier(**kwargs)
#    classifier = SVC(**kwargs)
    classifier.fit(training_data, training_target)

    pca = PCA(n_components=2)
    pca.fit(training_data)

    def print_results(data, target, shape):
        """Print the results of predictions.

        :param list data: Errors in the format of a matrix
        :param list target: The values that the data should correspond to
        """

        output = classifier.predict(data)

        components = pca.transform(data)

        right = 0

        for index, zipped in enumerate(zip(target, output)):
            want, result = zipped
            x, y = components[index]

            if want == result:
                color = 'b' if want else 'g'
                status = 'RIGHT'
                right += 1
            else:
                color = 'r' if result else 'm'
                status = 'WRONG'
            print '[%s] %i : %i -- %s : %s' % \
                (status, want, result, class_labels[want], class_labels[result])
            if x < -70 and y < -10:
                pyplot.scatter(x=x, y=y, marker=shape, facecolors='none', edgecolors=color)

        print '%f (%i/%i)' % (100.0 * right/len(target), right, len(target))

    print '\nTraining:\n'
    print_results(training_data, training_target, 'o')

    print '\nTesting:\n'
    print_results(testing_data, testing_target, '^')

    print len(testing_data[0])
    print len(testing_data[1])
    print classifier.n_layers_

    pyplot.savefig('/home/dabercro/public_html/full.pdf')

def main():
    """This is for testing."""
    if len(sys.argv) > 2:
        parameter = sys.argv[2]
    else:
        parameter = 'action'

    with open(sys.argv[1], 'r') as input_file:
        raw_data = json.load(input_file)

    get_classifier(raw_data, parameter, solver='lbfgs')


if __name__ == '__main__':
    main()
