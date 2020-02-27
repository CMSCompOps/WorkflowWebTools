import glob
import setuptools

import workflowwebtools

setuptools.setup(
    name='workflowwebtools',
    version=workflowwebtools.__version__,
    packages=setuptools.find_packages(),
    author='Daniel Abercrombie',
    author_email='dabercro@mit.edu',
    description='Provides a server for Production and Reprocessing operations',
    url='https://github.com/CMSCompOps/WorkflowWebTools',
    scripts=[s for s in glob.glob('bin/*') if not s.endswith('~')],
    package_data={
        'workflowwebtools': ['default/config.yml'],
        'workflowwebtools.web': ['static/*/*',
                                 'templates/*']
        },
    install_requires=[
        'requests',
        'cmstoolbox>=0.15.1',
        'CMSMonitoring',
        'more-itertools',
        'cherrypy',
        'mako',
        'numpy',
        'scikit-learn',
        'passlib',
        'bcrypt',
        'pyOpenSSL',
        'pytest>=4.4.2'
        'pyyaml>=5.1',
        'validators',
        'tabulate',
        'pymongo<3.5.0',
        'cx_Oracle'
        ]
    )
