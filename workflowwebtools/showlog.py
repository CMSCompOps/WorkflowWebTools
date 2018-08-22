"""
Generates content for the showlog webpage

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


from cmstoolbox.elasticsearch import search_logs


def give_logs(query, module='', limit=50):
    """Takes output from :py:func:`cmstoolbox.elasticsearch.search_logs`
    and organizes it to pass to a mako template

    :param str query: The query to pass to :py:func:`cmstoolbox.elasticsearch.search_logs`
    :param str module: The module to show
    :param int limit: The max number of logs to show on a single page
    :returns: dictionary with ['logs'], which is a list of logs, and ['meta'],
              which shows meta information of newest query result
    :rtype: dict
    """

    formtext = ('<form>Submit query: <input type="text" name="search"> '
                'Module: <input type="text" name="module" value="%s"> '
                'Logs Limit: <input type="text" name="limit" value = "%i"> '
                '<input type="submit" value="Submit"></form>' % (module, limit))

    if query == '':
        # Get form page
        return formtext

    else:
        output = search_logs(query)
        if not output:
            return 'No logs were found!<br>' + formtext

        texts = set()
        logs = list()

        for i in output:
            if len(texts) > limit:
                break
            if i['_source']['text'] in texts:
                continue

            if not module or i['_source']['subject'] == module:

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
