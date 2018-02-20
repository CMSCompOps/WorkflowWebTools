"""
The :py:mod:`paramsregression` module uses neural net classifiers to predict parameters
for error handling workflows.

.. Note::

   Regression part is a work in progress. Need more data.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sys
import json

from sklearn.neural_network import MLPClassifier

def get_classifier(raw_data, parameter, **kwargs):
    """
    Fit a classifier.
    If the module is run as a script,
    just print the training and test data output.
    Otherwise, return the classifier for farther use.

    .. Note::

       In development.

    :param dict raw_data: Raw data in the form of output from
                          :py:func:`actionshistorylink.dump_json`.
    :param str parameter: The parameter to classify.
    :param kwargs: These are kwargs for the ``sklearn.neural_network.MLPClassifier``
                   that is running underneath.
    :returns: Trained classifier model
    :rtype: sklearn.neural_network.MLPClassifier
    """

    primary_ids = sorted(set([key.split('/')[1] for key in raw_data.keys()]))

    # Only split samples when running interactive tests
    training_ids = primary_ids[0::2] if __name__ == '__main__' else primary_ids

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
    classifier.fit(training_data, training_target)

    if __name__ == '__main__':
        # Only does the following if running an interactive test
        def print_results(data, target):
            """Print the results of predictions.

            :param list data: Errors in the format of a matrix
            :param list target: The values that the data should correspond to
            """

            output = classifier.predict(data)

            right = 0

            for want, result in zip(target, output):

                if want == result:
                    status = 'RIGHT'
                    right += 1
                else:
                    status = 'WRONG'
                print '[%s] %i : %i -- %s : %s' % \
                    (status, want, result, class_labels[want], class_labels[result])

            print '%f (%i/%i)' % (100.0 * right/len(target), right, len(target))

        print '\nTraining:\n'
        print_results(training_data, training_target)

        print '\nTesting:\n'
        print_results(testing_data, testing_target)

    return classifier


def main():
    """This is for testing."""
    if len(sys.argv) > 2:
        parameter = sys.argv[2]
    else:
        parameter = 'action'

    with open(sys.argv[1], 'r') as input_file:
        raw_data = json.load(input_file)

    get_classifier(raw_data, parameter,
                   solver='lbfgs', hidden_layer_sizes=(100, 10))


if __name__ == '__main__':
    main()
