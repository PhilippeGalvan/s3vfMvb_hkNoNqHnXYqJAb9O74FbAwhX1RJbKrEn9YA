from setuptools import find_packages, setup

setup(
    name='test_sennder',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django',
        'redis',
        'requests',
    ],
    extras_require={
        "dev":  [
            'httpretty',
            'coverage',
            'flake8',
        ],
    }
)
