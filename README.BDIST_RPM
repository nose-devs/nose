On some platforms, brp-compress zips man pages without distutils knowing about
it. This results in an error when building an rpm for nose. The rpm build will
report either that an unpackaged file was found, or that an expected package
file was not found.

If you see such an error when using the bdist_rpm command, uncomment the
'install_script' line in the '[bdist_rpm]' section of nose's setup.cfg
file. This should fix the problem by fixing the man page filename in the
generated rpm spec file.