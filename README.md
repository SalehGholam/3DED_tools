# 3DED_tools
This is a simple GUI to be able to do 3DED on an FEI TEM. It just continuously tilts the stage with a certain speed from an angle to another. It has no connection to any camera; thus, one has to acquire images with a continuous mode manually. At the end, it also provides a report. The most important thing in this report is the tilt duration, with with you can calculate the integration angle for the 3DED.

For installations, I recommend (as a not-so-high-level user) to just install an Anaconda version which matches your operating system. For old PCs with WinXP, you can install up to python 3.4. Since usually it is prefered not to connect TEMs to the network, the easiest would be to just install Anaconda3 as it has some accompanying packages as well. Anaconda's archive can be found here:
https://repo.anaconda.com/archive/

I installed this one: https://repo.anaconda.com/archive/Anaconda3-2.3.0-Windows-x86.exe

For new PCs, just go for the best python/Anaconda version (which matches the operating system).

To control the microscope, the connection is made by temscript (https://github.com/niermann/temscript). So, its installation is necessary.

There are currently 2 files, which are written for PyQt4 (old PCs) and PyQt5.
