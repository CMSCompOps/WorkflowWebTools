"""
Generates content for the showlog webpage

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


from CMSToolBox.elasticsearch import search_logs


def give_logs(query):
    """Takes output from :py:func:`search_logs` and organizes it to pass to a mako template

    :param str query: The query to pass to :py:func:`search_logs`
    :returns: dictionary with ['logs'], which is a list of logs, and ['meta'],
              which shows meta information of newest query result
    :rtype: dict
    """

    formtext = ('<form>Submit query: <input type="text" name="search"> '
                '<input type="submit" value="Submit"></form>')

    if query == '':
        # Get form page
        return formtext

    else:
        output = search_logs(query)
        if len(output) == 0:
            return 'No logs were found!<br>' + formtext

        texts = set()
        logs = list()

        for i in output:
            if len(texts) > 50:
                break
            if i['_source']['text'] in texts:
                continue

            logs.append(
                {
                    'subject': i['_source']['subject'],
                    'date':    i['_source']['date'],
                    'text':    i['_source']['text'].split('\n')
                }
            )

            texts.add(i['_source']['text'])

        return {
            'logs': logs,
            'meta': output[0]['_source']['meta'].split('\n')
            }
