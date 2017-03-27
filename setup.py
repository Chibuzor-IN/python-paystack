from setuptools import setup

setup(name = 'python_paystack',
      version = '0.9.7',
      description = 'A Paystack API wrapper',
      url = '',
      author = 'Nwalor Chibuzor',
      author_email = 'nwalorc@gmail.com',
      license = 'MIT',
      packages = ['python_paystack'],
      install_requires=[
          'requests',
          'validators',
          'jsonpickle',
          'forex_python'
          ]
    )
