from setuptools import setup

setup(name='mets2handle',
      version='0.1',
      description='Tool create ePIC PIDs based on mets files',
      url='https://github.com/AV-EFI/mets2handle_dk',
      author='Henry Bieker, Sven Bingert',
      packages=['mets2handle'],
      zip_safe=False,
      install_requires=[
        'typing',
        'lxml==4.9.2',
        'requests',
        'urllib3==2.0.3',
        'uuid'
        ]
    )
