from setuptools import setup

setup(name='python_paystack',
      version='1.0.6',
      description='A Paystack API wrapper',
      url='',
      author='Nwalor Chibuzor',
      author_email='nwalorc@gmail.com',
      license='MIT',
      packages=['python_paystack'],
      install_requires=[
          'requests',
          'validators',
          'jsonpickle',
          'forex_python'
          ]
     )
