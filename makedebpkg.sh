#!/bin/bash
cd docs/
make html
cd -

python setup.py --command-packages=stdeb.command sdist_dsc

version=$(cat pifacerelayplus/version.py | sed 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/')
cd deb_dist/pifacerelayplus-$version/

cp {../../dpkg-files,debian}/control
cp {../../dpkg-files,debian}/copyright
cp {../../dpkg-files,debian}/rules
cp {../../dpkg-files,debian}/python-pifacerelayplus.install
cp {../../dpkg-files,debian}/python3-pifacerelayplus.install

ls ../../examples/ | while read example
do
    echo ../../examples/$example >> debian/python-pifacerelayplus.examples
    echo ../../examples/$example >> debian/python3-pifacerelayplus.examples
done

dpkg-buildpackage -us -uc
