#!/bin/bash
make xsim &&
/bin/sh -c "exit `grep -i "^error" -c xsim.log`"
