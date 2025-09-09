from setuptools import setup, find_packages
import os

setup(
    name="LunchBot",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests==2.31.0',
        'python-dotenv==1.0.0',
        'cryptography==41.0.7',
        'google-api-python-client==2.104.0',
        'google-auth-oauthlib==1.1.0',
        'google-auth-httplib2==0.1.1',
        'google-auth==2.23.4'
    ],
    entry_points={
        'console_scripts': [
            'lunchbot=main:main',
        ],
    },
    author="Your Name",
    description="Telegram bot for lunch orders",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)