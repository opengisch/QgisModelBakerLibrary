#!/bin/bash
LIBS_DIR="modelbaker/libs"

PGSERVICEPARSER=("pgserviceparser" "2.2.1")
TOPPINGMAKER=("toppingmaker" "1.7.0")

XSDATA=("xsdata" "26.2")
TYPINGEXTENSIONS=("typing-extensions" "4.16.0")

PACKAGES=(
  PGSERVICEPARSER[@]
  TOPPINGMAKER[@]
  XSDATA[@]
  TYPINGEXTENSIONS[@]
)

#recreate lib folder
rm -rf "$LIBS_DIR"
mkdir -p "$LIBS_DIR"

for PACKAGE in ${PACKAGES[@]}; do
  echo download and unpack ${!PACKAGE:0:1} with version ${!PACKAGE:1:1}
  #create temp folder
  mkdir -p temp
  #download the wheel
  pip download -v ${!PACKAGE:0:1}==${!PACKAGE:1:1} --only-binary :all: -d temp/
  #unpack all the wheels found (means including dependencies)
  unzip -o "temp/*.whl" -d $LIBS_DIR
  #remove temp folder
  rm -r temp
done

# ili2py not yet on pypi - we get it from the repo
COMMIT="c0e815e2fec9b5a5410633c291098de393529160"
echo get ili2py on commit "$COMMIT"
git clone -q https://github.com/rudert-geoinformatik/ili2py.git temp_ili2py_git
cd temp_ili2py_git && git checkout -q "$COMMIT" && cd - > /dev/null
mv temp_ili2py_git/src/ili2py "$LIBS_DIR/"
rm -rf temp_ili2py_git
echo ili2py stored

#set write rights to group (because qgis-plugin-ci needs it)
chmod -R g+w $LIBS_DIR

#create the __init__.py in libs folder
cd $LIBS_DIR
touch __init__.py
