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
        'cmstoolbox>=0.12.0',
        'more-itertools<6.0.0',
        'cherrypy<18.0.0',
        'mako',
        'numpy>=1.14.5,<1.17',
        'scikit-learn',
        'passlib>=1.6',
        'bcrypt',
        'pyOpenSSL',
        'pytest>=4.4.2,<5.0'
        'pyyaml>=5.1',
        'validators',
        'tabulate',
        'pymongo<3.5.0',
        'cx_Oracle',
        'pandas<0.25.0',
        'keras'
        ]
    )
