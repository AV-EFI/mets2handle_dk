from setuptools import setup

setup(name='mets2handle',
      version='0.1',
      description='Tool create ePIC PIDs based on mets files',
      url='https://github.com/AV-EFI/mets2handle_dk',
      author='Henry Bieker, Sven Bingert',
      packages=['mets2handle'],
      zip_safe=False,
      install_requires=[
        'typing==3.7.4.3',
        'lxml==4.9.2',
        'requests==2.31.0',
        'urllib3==2.0.3',
        'uuid==1.30'
        ]
    )
