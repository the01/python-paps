#!/usr/bin/env bash
coverage run --source ./ --omit="setup.py" --branch -m py.test tests/
coverage report --omit="tests/*"
coverage html --omit="tests/*" -d coverage/