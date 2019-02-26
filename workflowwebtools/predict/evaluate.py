# pylint: disable=missing-docstring, too-complex, invalid-name, too-many-branches, too-many-locals

"""
A module that evaluates a model and returns the prediction
"""

import os
import random
import itertools

import numpy as np
import pandas as pd
import keras as K


def modified_site_name(site):
    site_name = site.split('_')[:-1]
    s = ''
    for i in site_name:
        s = s+i+'_'
    s = s.rstrip('_')
    return s

def build_table(df, template_table):
    sparse_df = template_table.copy()

    tier0_sites, tier1_sites, tier2_sites, tier3_sites = [], [], [], []
    for i in sparse_df.keys():
        if i != 'NA':
            if i[1] == '0':
                tier0_sites.append(i)
            elif i[1] == '1':
                tier1_sites.append(i)
            elif i[1] == '2':
                tier2_sites.append(i)
            elif i[1] == '3':
                tier3_sites.append(i)

    n0, n1, n2, n3 = len(tier0_sites), len(tier1_sites), len(tier2_sites), len(tier3_sites)
    for exit_code, site_dict in zip(df.keys(), df.values()):
        exit_code = int(exit_code)
        for site, count in site_dict.items():

            chosen_site = None
            site_present_in_training_data = site in sparse_df.keys()
            if not site_present_in_training_data:

                site = modified_site_name(site)
                cond = site in sparse_df.keys()
                if cond:
                    chosen_site = site

                print "Detected a site %s which was not present in the training dataset" % site
                print "We would use a proxy site for this based on whether it is T1, T2 or T3"
                tier = site.split("_")[0][1]
                if chosen_site is None:
                    if tier == '1':
                        chosen_num = random.randint(0, n1-1)
                        chosen_site = tier1_sites[chosen_num]
                    elif tier == '2':
                        chosen_num = random.randint(0, n2-1)
                        chosen_site = tier2_sites[chosen_num]
                        print 'The chosen site is ', chosen_site
                    elif tier == '3':
                        chosen_num = random.randint(0, n3-1)
                        chosen_site = tier3_sites[chosen_num]
                        print 'The chosen site is ', chosen_site
                    elif tier == '0':
                        chosen_num = random.randint(0, n0-1)
                        chosen_site = tier0_sites[chosen_num]
                        print 'The chosen site is ', chosen_site
                    else:
                        continue
                if chosen_site is None:
                    chosen_site = site

                if np.isnan(count) or np.isnan(sparse_df.loc[exit_code, chosen_site]):
                    sparse_df.loc[exit_code, chosen_site] = 0
                else:
                    sparse_df.loc[exit_code, chosen_site] = count

    return sparse_df


def list_of_sites(x):
    return [item.keys() for item in x] or ['NA']

def build_table_flatten(x):
    d_outer = []

    for column in x:

        for item in x[column]:
            d_outer.append(item)

    return d_outer


def pred(errors):
    # Needs all of these files to be local
    for filename in ['sparse_table.csv', 'actionfile.txt', 'my_model.h5']:
        if not os.path.exists(filename):
            return ['TBD']

    df = pd.DataFrame(columns=('workflow', 'errors'))
    base_data = []
    for i in errors:
        it = i.items()
        base_data.extend(it)

    for i, dat in enumerate(base_data):
        workflow, error_dict = dat[0], dat[1]

        if 'NotReported' in error_dict:
            error_dict[-1] = error_dict.pop('NotReported')

        df.loc[i] = [workflow, error_dict]

    template_table = pd.read_csv("sparse_table.csv").set_index("Unnamed: 0")
    template_table[:] = 0
    df['errors_sites_exit_codes'] = df['errors'].apply(lambda x: x.keys() if x else ['0'])

    df['errors_sites_dict'] = df['errors'].apply(lambda x: x.values() if x else [{'NA': 0}])

    df['errors_sites_list'] = df['errors_sites_dict'].apply(list_of_sites)

    list2d = df['errors_sites_exit_codes'].tolist()

    sites_exit_codes = sorted(set(list(itertools.chain.from_iterable(list2d))), key=int)
    sites_exit_codes = [str(x) for x in sites_exit_codes]

    list2d_step1 = df['errors_sites_list'].tolist()
    list2d_step2 = list(itertools.chain.from_iterable(list2d_step1))
    site_names = sorted(set(list(itertools.chain.from_iterable(list2d_step2))))
    site_names = [str(x) for x in site_names]

    df['table_sites'] = df['errors'].apply(
        lambda x: build_table(x, template_table))
    df['table_sites_flatten'] = df['table_sites'].apply(build_table_flatten)
    x_dataframe = df.loc[:, "table_sites_flatten"]
    x_matrix = x_dataframe.values
    feature_size = len(x_matrix[0])
    res = []
    clip_length = len(x_matrix[0])
    for i in x_matrix:
        i_clipped = i[:clip_length]
        res.extend(i_clipped)

    res = np.asarray(res).reshape(-1, feature_size)
    mask = ~np.any(pd.isnull(res), axis=1)
    res = res[mask]

    model = K.models.load_model('my_model.h5')
    predicted_actions_encoded = model.predict(np.array(np.asfarray(res)))
    predicted_actions_encoded = np.round(predicted_actions_encoded)

    action_code_dictionary = {}
    a = np.genfromtxt("actionfile.txt", delimiter='\t', dtype=str)
    b = list(i.split('   ') for i in a)
    for i in b:

        action_code_dictionary[int(i[1])] = i[0]

    predicted_actions = []
    for i in predicted_actions_encoded:
        pos = np.argmax(i)

        if pos in action_code_dictionary:
            predicted_actions.append(action_code_dictionary[pos])
        else:
            predicted_actions.append(-1)

    K.backend.clear_session()

    return predicted_actions


def predict(wf_obj):
    """
    Takes the errors for a workflow and makes an action prediction
    :param workflowwebtool.workflowinfo.WorkflowInfo wf_obj:
        The WorkflowInfo object that we want to perform a prediction on
    :returns: Prediction results to be passed back to a browser
    :rtype: dict
    """

    return {
        'Action': pred([wf_obj.get_errors(True)])[0]
    }
