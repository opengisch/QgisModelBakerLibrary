#!/bin/bash
LIBS_DIR="modelbaker/libs"

PGSERVICEPARSER=("pgserviceparser" "1.1.0")
TOPPINGMAKER=("toppingmaker" "1.0.2")

PACKAGES=(
  PGSERVICEPARSER[@]
  TOPPINGMAKER[@]
)

#create lib folder
mkdir -p $LIBS_DIR

for PACKAGE in ${PACKAGES[@]}; do
  echo download and unpack ${!PACKAGE:0:1} with version ${!PACKAGE:1:1}
  #create temp folder
  mkdir -p temp
  #download the wheel
  pip download -v ${!PACKAGE:0:1}==${!PACKAGE:1:1} --only-binary :all: -d temp/
  #unpack the wheel
  unzip -o temp/${!PACKAGE:0:1}*.whl -d $LIBS_DIR
  #remove temp folder
  rm -r temp
  #set write rights to group (because qgis-plugin-ci needs it)
  chmod -R g+w $LIBS_DIR
done

#create the __init__.py in libs folder
cd $LIBS_DIR
touch __init__.py
