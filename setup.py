from distutils.core import setup

setup(
    name='PCR',
    version='1.0',
    packages=['PCR'],
    url='https://gitlab.lrz.de/000000003B9B9936/pcr',
    license='MIT',
    description='Tools for parallelized research with cloud resources.',
    python_requires='>=3.5',
    install_requires=[
        'boto3>=1.14.29',
    ],
)
