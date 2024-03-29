from setuptools import setup

setup(name='mets2handle',
      version='0.1',
      description='Tool create ePIC PIDs based on mets files',
      url='https://github.com/AV-EFI/mets2handle_dk',
      author='Henry Beiker, Sven Bingert',
      packages=['mets2handle'],
      zip_safe=False,
      install_requires=[
        'typing==3.7.4.3',
        'lxml==4.9.2',
        'requests==2.31.0',
        'urllib3==2.0.3',
        'uuid==1.30',
        'pycountry==22.3.5'
        ],
      entry_points={
          'console_scripts': [
              'metstohandle=mets2handle.metstohandle:cli_entry_point',
          ],
      }
    )
