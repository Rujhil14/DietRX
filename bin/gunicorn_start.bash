#!/bin/bash

NAME="dietrx"                                  # Name of the application
SOCKFILE=/home/iiitd/Dietrx/bin/gunicorn.sock  # we will communicte using this unix socket
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
FLASK_DIR=/home/iiitd/Dietrx

echo "Starting $NAME"

# Activate the virtual environment
cd $FLASK_DIR
source activate dietrx

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Flask Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec /home/iiitd/miniconda3/envs/dietrx/bin/gunicorn app:app \
  --name $NAME \
  --workers $NUM_WORKERS \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-
