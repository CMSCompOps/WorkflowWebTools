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
        'cmstoolbox',
        'cherrypy<18.0.0',
        'mako',
        'numpy>=1.6.1',
        'scipy==1.1.0',
        'sklearn',
        'passlib>=1.6',
        'bcrypt',
        'pyOpenSSL',
        'pyyaml',
        'validators',
        'tabulate',
        'pymongo<3.5.0',
        'cx_Oracle',
        'pandas',
        'keras',
        'tensorflow'
        ]
    )
