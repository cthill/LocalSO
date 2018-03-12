# LocalSO Installer

The LocalSO installer is a program for adding entries to `C:\Windows\System32\drivers\etc\hosts`. This allows the Stick Online client to connect to the LocalSO server.

This folder contains the source code for two versions of the LocalSO Windows installer. The first version is a batch file. The second is a C++ program.

If you are building the C++ version with Visual Studio, be sure to set the `UAC Execution Level` to `requireAdministrator (/level='requireAdministrator')` in the manifest.
