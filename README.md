# Example of saving provenance of hiphive fit using AiiDA

**without writing any formal plugin**

Code snippets are taken from: https://hiphive.materialsmodeling.org/tutorial/index.html.

This repository demonstrates how to wrap hiphive routines inside AiiDA's `@calcfunction` and `@workfunction` in order to preserve the result and its provenance. Such functionalities do not require writing any dedicated plugin code, although putting the routines into a Python package may still be highly desirable.

`datagen.py` can be run to generate and store the example fit.

`load-fcp.py` contains example code for loading the force constant potential from an archive export.

To create an archive, run:

```
verdi archive create -N <uuid1> <uuid2> -- hiphive-example.aiida
```


where `<uuid1>` and `<uuid2>` are the UUIDs of the two nodes printed at the end of running `datagen.py`.

Note that running `datagen.py` can be done with a temporary in-memory profile without a fully working AiiDA installation. However, at the moment, it is not possible to export data into an archive from such an in-memory profile.

The `load-fcp.py` can run by any `aiida-core>=2.0` installation; there is no need to install any non-Python dependencies.

Provenance graph:
![](fcp-provenance.png)
