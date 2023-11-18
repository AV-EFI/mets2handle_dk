# Mets2Handle 

Mets2Handle allows to create PIDs from XMLs

### Usage

```
pip install .
metstohandle -c <path_to_credentials> -o <output_mets.xml> <input_mets.xml>
```

If multiple DataObjects for the same Work and Version shall be
registered, make sure that they all use the same handle for Work and
Version. After registering the first DataObject, grab handles for Work
and Version from the generated METS and pass them as parameters like
this:

```
metstohandle -c <path_to_credentials> -v <version_pid> -w <work_pid> \
    -o <output_mets.xml> <input_mets.xml>
```

Use this package as a library as follows:

```
import mets2handle
filename = <path_to_file>
res = mets2handle.m2h(filename)
```
