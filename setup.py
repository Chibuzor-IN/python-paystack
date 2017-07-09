from setuptools import setup

setup(name='python_paystack',
      version='1.2.0',
      description='A Paystack API wrapper',
      url='',
      author='Nwalor Chibuzor',
      author_email='nwalorc@gmail.com',
      license='MIT',
      packages=['python_paystack', 'python_paystack.objects'],
      install_requires=[
          'requests',
          'validators',
          'jsonpickle',
          'forex_python'
          ]
     )
