#!/bin/bash

while ! nc -z tema2_db 5432; do sleep 1; done

python3 main.py
