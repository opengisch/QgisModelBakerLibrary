#!/usr/bin/env bash
#***************************************************************************
#                             -------------------
#       begin                : 2017-08-24
#       git sha              : :%H$
#       copyright            : (C) 2017 by OPENGIS.ch
#       email                : info@opengis.ch
#***************************************************************************
#
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************

set -e

/usr/src/tests/testdata/mssql/setup-mssql.sh

# Default to postgres12 unless another host has been defined (i.e. postgres11 from travis test matrix / docker-compose)
export PGHOST=${PGHOST:-postgres12}

# rationale: Wait for postgres container to become available
echo "Wait a moment while loading the PG database: ${PGHOST}"
until PGPASSWORD='docker' psql -h $PGHOST -U docker > /dev/null 2>&1; do
  printf " 🐘"
  sleep 2
done
echo ""

pushd /usr/src
DEFAULT_PARAMS='-v'
xvfb-run pytest-3 ${@:-`echo $DEFAULT_PARAMS`} $1 $2
popd
