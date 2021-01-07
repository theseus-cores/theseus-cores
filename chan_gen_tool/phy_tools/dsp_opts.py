#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:20:20 2017

@author: phil
"""
import ipdb
from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

def opcode_opts(opcode):
    opcode = opcode.upper()
    opcode = opcode.replace(" ", "")

    alumode = 0
    inmode_diff = None
    if opcode == '(A+D)':
        alumode = 0
    elif opcode == '(A+D)*B':
        alumode = 0
    elif opcode == '(A+D)*B+C':
        alumode = 0
    elif opcode == '(A+D)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*B+P':
        alumode = 0
    elif opcode == '(A+D)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*B+P>>17':
        alumode = 0
    elif opcode == '(A+D)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*B+PCIN':
        alumode = 0
    elif opcode == '(A+D)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(A+D)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+C':
        alumode = 0
    elif opcode == '(A+D)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+P':
        alumode = 0
    elif opcode == '(A+D)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(A+D)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(A+D)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+C':
        alumode = 0
    elif opcode == '(A+D)+C+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+P':
        alumode = 0
    elif opcode == '(A+D)+P+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+P>>17':
        alumode = 0
    elif opcode == '(A+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+PCIN':
        alumode = 0
    elif opcode == '(A+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(A+D)+PCIN>>17':
        alumode = 0
    elif opcode == '(A+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)':
        alumode = 0
    elif opcode == '(ACIN+D)*B':
        alumode = 0
    elif opcode == '(ACIN+D)*B+C':
        alumode = 0
    elif opcode == '(ACIN+D)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+P':
        alumode = 0
    elif opcode == '(ACIN+D)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+P>>17':
        alumode = 0
    elif opcode == '(ACIN+D)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+PCIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(ACIN+D)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+C':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+P':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(ACIN+D)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+C':
        alumode = 0
    elif opcode == '(ACIN+D)+C+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+P':
        alumode = 0
    elif opcode == '(ACIN+D)+P+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+P>>17':
        alumode = 0
    elif opcode == '(ACIN+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+PCIN':
        alumode = 0
    elif opcode == '(ACIN+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(ACIN+D)+PCIN>>17':
        alumode = 0
    elif opcode == '(ACIN+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)':
        alumode = 0
    elif opcode == '(D+A)*B':
        alumode = 0
    elif opcode == '(D+A)*B+C':
        alumode = 0
    elif opcode == '(D+A)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*B+P':
        alumode = 0
    elif opcode == '(D+A)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*B+P>>17':
        alumode = 0
    elif opcode == '(D+A)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*B+PCIN':
        alumode = 0
    elif opcode == '(D+A)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(D+A)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+C':
        alumode = 0
    elif opcode == '(D+A)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+P':
        alumode = 0
    elif opcode == '(D+A)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(D+A)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(D+A)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+C':
        alumode = 0
    elif opcode == '(D+A)+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+P':
        alumode = 0
    elif opcode == '(D+A)+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+P>>17':
        alumode = 0
    elif opcode == '(D+A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+PCIN':
        alumode = 0
    elif opcode == '(D+A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+A)+PCIN>>17':
        alumode = 0
    elif opcode == '(D+A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)':
        alumode = 0
    elif opcode == '(D+ACIN)*B':
        alumode = 0
    elif opcode == '(D+ACIN)*B+C':
        alumode = 0
    elif opcode == '(D+ACIN)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+P':
        alumode = 0
    elif opcode == '(D+ACIN)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+P>>17':
        alumode = 0
    elif opcode == '(D+ACIN)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+PCIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(D+ACIN)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+C':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+P':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(D+ACIN)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+C':
        alumode = 0
    elif opcode == '(D+ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+P':
        alumode = 0
    elif opcode == '(D+ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+P>>17':
        alumode = 0
    elif opcode == '(D+ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+PCIN':
        alumode = 0
    elif opcode == '(D+ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D+ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == '(D+ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)':
        alumode = 0
    elif opcode == '(D-A)*B':
        alumode = 0
    elif opcode == '(D-A)*B+C':
        alumode = 0
    elif opcode == '(D-A)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*B+P':
        alumode = 0
    elif opcode == '(D-A)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*B+P>>17':
        alumode = 0
    elif opcode == '(D-A)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*B+PCIN':
        alumode = 0
    elif opcode == '(D-A)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(D-A)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+C':
        alumode = 0
    elif opcode == '(D-A)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+P':
        alumode = 0
    elif opcode == '(D-A)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(D-A)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(D-A)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+C':
        alumode = 0
    elif opcode == '(D-A)+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+P':
        alumode = 0
    elif opcode == '(D-A)+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+P>>17':
        alumode = 0
    elif opcode == '(D-A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+PCIN':
        alumode = 0
    elif opcode == '(D-A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-A)+PCIN>>17':
        alumode = 0
    elif opcode == '(D-A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)':
        alumode = 0
    elif opcode == '(D-ACIN)*B':
        alumode = 0
    elif opcode == '(D-ACIN)*B+C':
        alumode = 0
    elif opcode == '(D-ACIN)*B+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+P':
        alumode = 0
    elif opcode == '(D-ACIN)*B+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+P>>17':
        alumode = 0
    elif opcode == '(D-ACIN)*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+PCIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*B+PCIN>>17':
        alumode = 0
    elif opcode == '(D-ACIN)*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+C':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+P':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+P>>17':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+PCIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == '(D-ACIN)*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+C':
        alumode = 0
    elif opcode == '(D-ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+P':
        alumode = 0
    elif opcode == '(D-ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+P>>17':
        alumode = 0
    elif opcode == '(D-ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+PCIN':
        alumode = 0
    elif opcode == '(D-ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == '(D-ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == '(D-ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == '-((A+D))':
        alumode = 3
    elif opcode == '-((A+D)*B)':
        alumode = 3
    elif opcode == '-((A+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == '-((A+D)*BCIN)':
        alumode = 3
    elif opcode == '-((A+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-((A+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-((ACIN+D))':
        alumode = 3
    elif opcode == '-((ACIN+D)*B)':
        alumode = 3
    elif opcode == '-((ACIN+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == '-((ACIN+D)*BCIN)':
        alumode = 3
    elif opcode == '-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-((ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+A))':
        alumode = 3
    elif opcode == '-((D+A)*B)':
        alumode = 3
    elif opcode == '-((D+A)*B+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+A)*BCIN)':
        alumode = 3
    elif opcode == '-((D+A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+A)+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+ACIN))':
        alumode = 3
    elif opcode == '-((D+ACIN)*B)':
        alumode = 3
    elif opcode == '-((D+ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+ACIN)*BCIN)':
        alumode = 3
    elif opcode == '-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-((D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-((D-A))':
        alumode = 3
    elif opcode == '-((D-A)*B)':
        alumode = 3
    elif opcode == '-((D-A)*B+CARRYIN)':
        alumode = 3
    elif opcode == '-((D-A)*BCIN)':
        alumode = 3
    elif opcode == '-((D-A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-((D-A)+CARRYIN)':
        alumode = 3
    elif opcode == '-((D-ACIN))':
        alumode = 3
    elif opcode == '-((D-ACIN)*B))':
        alumode = 3
    elif opcode == '-((D-ACIN)*B+CARRYIN))':
        alumode = 3
    elif opcode == '-((D-ACIN)*BCIN))':
        alumode = 3
    elif opcode == '-((D-ACIN)*BCIN+CARRYIN))':
        alumode = 3
    elif opcode == '-((D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-(A)':
        alumode = 3
    elif opcode == '-(A*B)':
        alumode = 3
    elif opcode == '-(A*B+CARRYIN)':
        alumode = 3
    elif opcode == '-(A*BCIN)':
        alumode = 3
    elif opcode == '-(A*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(A+CARRYIN)':
        alumode = 3
    elif opcode == '-(A+D)':
        alumode = 3
    elif opcode == '-(A+D)*B':
        alumode = 3
    elif opcode == '-(A+D)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(A+D)*BCIN':
        alumode = 3
    elif opcode == '-(A+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(A+D)-CARRYIN':
        alumode = 3
    elif opcode == '-(ACIN)':
        alumode = 3
    elif opcode == '-(ACIN*B)':
        alumode = 3
    elif opcode == '-(ACIN*B+CARRYIN)':
        alumode = 3
    elif opcode == '-(ACIN*BCIN)':
        alumode = 3
    elif opcode == '-(ACIN*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(ACIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(ACIN+D)':
        alumode = 3
    elif opcode == '-(ACIN+D)*B':
        alumode = 3
    elif opcode == '-(ACIN+D)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(ACIN+D)*BCIN':
        alumode = 3
    elif opcode == '-(ACIN+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == '-(B*(A+D))':
        alumode = 3
    elif opcode == '-(B*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*(ACIN+D))':
        alumode = 3
    elif opcode == '-(B*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*(D+A))':
        alumode = 3
    elif opcode == '-(B*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*(D+ACIN))':
        alumode = 3
    elif opcode == '-(B*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*(D-A))':
        alumode = 3
    elif opcode == '-(B*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*(D-ACIN))':
        alumode = 3
    elif opcode == '-(B*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*A)':
        alumode = 3
    elif opcode == '-(B*A+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*ACIN)':
        alumode = 3
    elif opcode == '-(B*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(B*D)':
        alumode = 3
    elif opcode == '-(B*D+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(A+D))':
        alumode = 3
    elif opcode == '-(BCIN*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(ACIN+D))':
        alumode = 3
    elif opcode == '-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(D+A))':
        alumode = 3
    elif opcode == '-(BCIN*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(D+ACIN))':
        alumode = 3
    elif opcode == '-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(D-A))':
        alumode = 3
    elif opcode == '-(BCIN*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*(D-ACIN))':
        alumode = 3
    elif opcode == '-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*A)':
        alumode = 3
    elif opcode == '-(BCIN*A+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*ACIN)':
        alumode = 3
    elif opcode == '-(BCIN*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(BCIN*D)':
        alumode = 3
    elif opcode == '-(BCIN*D+CARRYIN)':
        alumode = 3
    elif opcode == '-(C)':
        alumode = 3
    elif opcode == '-(C+CARRYCASCIN)':
        alumode = 3
    elif opcode == '-(C+CARRYIN)':
        alumode = 3
    elif opcode == '-(C+CONCAT)':
        alumode = 3
    elif opcode == '-(C+CONCAT+CARRYCASCIN)':
        alumode = 3
    elif opcode == '-(C+CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == '-(C+P)':
        alumode = 3
    elif opcode == '-(C+P+CARRYCASCIN)':
        alumode = 3
    elif opcode == '-(C+P+CARRYIN)':
        alumode = 3
    elif opcode == '-(CARRYIN)':
        alumode = 3
    elif opcode == '-(CONCAT)':
        alumode = 3
    elif opcode == '-(CONCAT+C)':
        alumode = 2
    elif opcode == '-(CONCAT+C+CARRYCASCIN)':
        alumode = 2
    elif opcode == '-(CONCAT+C+CARRYIN)':
        alumode = 2
    elif opcode == '-(CONCAT+CARRYCASCIN)':
        alumode = 2
    elif opcode == '-(CONCAT+CARRYIN)':
        alumode = 2
    elif opcode == '-(D)':
        alumode = 3
    elif opcode == '-(D*B)':
        alumode = 3
    elif opcode == '-(D*B+CARRYIN)':
        alumode = 3
    elif opcode == '-(D*BCIN)':
        alumode = 3
    elif opcode == '-(D*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == '-(D+A)':
        alumode = 3
    elif opcode == '-(D+A)*B':
        alumode = 3
    elif opcode == '-(D+A)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(D+A)*BCIN':
        alumode = 3
    elif opcode == '-(D+A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(D+A)-CARRYIN':
        alumode = 3
    elif opcode == '-(D+ACIN)':
        alumode = 3
    elif opcode == '-(D+ACIN)*B':
        alumode = 3
    elif opcode == '-(D+ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(D+ACIN)*BCIN':
        alumode = 3
    elif opcode == '-(D+ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-(D+CARRYIN)':
        alumode = 3
    elif opcode == '-(D-A)':
        alumode = 3
    elif opcode == '-(D-A)*B':
        alumode = 3
    elif opcode == '-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(D-A)*BCIN':
        alumode = 3
    elif opcode == '-(D-A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(D-A)-CARRYIN':
        alumode = 3
    elif opcode == '-(D-ACIN)':
        alumode = 3
    elif opcode == '-(D-ACIN)*B':
        alumode = 3
    elif opcode == '-(D-ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == '-(D-ACIN)*BCIN':
        alumode = 3
    elif opcode == '-(D-ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-(P)':
        alumode = 2
    elif opcode == '-(P+C)':
        alumode = 2
    elif opcode == '-(P+C+CARRYCASCIN)':
        alumode = 2
    elif opcode == '-(P+C+CARRYIN)':
        alumode = 2
    elif opcode == '-(P+CARRYCASCIN)':
        alumode = 2
    elif opcode == '-(P+CARRYIN)':
        alumode = 2
    elif opcode == '-A':
        alumode = 0
    elif opcode == '-A*B':
        alumode = 0
    elif opcode == '-A*B-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-A*BCIN':
        alumode = 0
    elif opcode == '-A*BCIN-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-A-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-ACIN':
        alumode = 3
    elif opcode == '-ACIN*B':
        alumode = 3
    elif opcode == '-ACIN*B-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-ACIN*BCIN':
        alumode = 3
    elif opcode == '-ACIN*BCIN-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-ACIN-CARRYIN':
        alumode = 3
        inmode = ~8
    elif opcode == '-B*(A+D)':
        alumode = 3
    elif opcode == '-B*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == '-B*(ACIN+D)':
        alumode = 3
    elif opcode == '-B*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == '-B*(D+A)':
        alumode = 3
    elif opcode == '-B*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == '-B*(D+ACIN)':
        alumode = 3
    elif opcode == '-B*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-B*(D-A)':
        alumode = 3
    elif opcode == '-B*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == '-B*(D-ACIN)':
        alumode = 3
    elif opcode == '-B*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-B*A':
        alumode = 3
    elif opcode == '-B*A-CARRYIN':
        alumode = 3
    elif opcode == '-B*ACIN':
        alumode = 3
    elif opcode == '-B*ACIN-CARRYIN':
        alumode = 3
    elif opcode == '-B*D':
        alumode = 3
    elif opcode == '-B*D-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(A+D)':
        alumode = 3
    elif opcode == '-BCIN*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(ACIN+D)':
        alumode = 3
    elif opcode == '-BCIN*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(D+A)':
        alumode = 3
    elif opcode == '-BCIN*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(D+ACIN)':
        alumode = 3
    elif opcode == '-BCIN*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(D-A)':
        alumode = 3
    elif opcode == '-BCIN*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*(D-ACIN)':
        alumode = 3
    elif opcode == '-BCIN*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*A':
        alumode = 3
    elif opcode == '-BCIN*A-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*ACIN':
        alumode = 3
    elif opcode == '-BCIN*ACIN-CARRYIN':
        alumode = 3
    elif opcode == '-BCIN*D':
        alumode = 3
    elif opcode == '-BCIN*D-CARRYIN':
        alumode = 3
    elif opcode == '-C':
        alumode = 3
    elif opcode == '-C-CARRYCASCIN':
        alumode = 3
    elif opcode == '-C-CARRYIN':
        alumode = 3
    elif opcode == '-C-CONCAT':
        alumode = 3
    elif opcode == '-C-CONCAT-CARRYCASCIN':
        alumode = 3
    elif opcode == '-C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == '-C-P':
        alumode = 3
    elif opcode == '-C-P-CARRYCASCIN':
        alumode = 3
    elif opcode == '-C-P-CARRYIN':
        alumode = 3
    elif opcode == '-CARRYIN':
        alumode = 3
    elif opcode == '-CONCAT':
        alumode = 3
    elif opcode == '-CONCAT-C':
        alumode = 3
    elif opcode == '-CONCAT-C-CARRYCASCIN':
        alumode = 3
    elif opcode == '-CONCAT-C-CARRYIN':
        alumode = 3
    elif opcode == '-CONCAT-CARRYCASCIN':
        alumode = 3
    elif opcode == '-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == '-D':
        alumode = 3
    elif opcode == '-D*B':
        alumode = 3
    elif opcode == '-D*B-CARRYIN':
        alumode = 3
    elif opcode == '-D*BCIN':
        alumode = 3
    elif opcode == '-D*BCIN-CARRYIN':
        alumode = 3
    elif opcode == '-D-CARRYIN':
        alumode = 3
    elif opcode == '-P':
        alumode = 3
    elif opcode == '-P-C':
        alumode = 3
    elif opcode == '-P-C-CARRYCASCIN':
        alumode = 3
    elif opcode == '-P-C-CARRYIN':
        alumode = 3
    elif opcode == '-P-CARRYCASCIN':
        alumode = 3
    elif opcode == '-P-CARRYIN':
        alumode = 3
    elif opcode == '0':
        alumode = 0
    elif opcode == 'A':
        alumode = 0
    elif opcode == 'A*B':
        alumode = 0
    elif opcode == 'A*B+C':
        alumode = 0
    elif opcode == 'A*B+C+CARRYIN':
        alumode = 0
    elif opcode == 'A*B+CARRYIN':
        alumode = 0
    elif opcode == 'A*B+P':
        alumode = 0
    elif opcode == 'A*B+P+CARRYIN':
        alumode = 0
    elif opcode == 'A*B+P>>17':
        alumode = 0
    elif opcode == 'A*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'A*B+PCIN':
        alumode = 0
    elif opcode == 'A*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'A*B+PCIN>>17':
        alumode = 0
    elif opcode == 'A*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN':
        alumode = 0
    elif opcode == 'A*BCIN+C':
        alumode = 0
    elif opcode == 'A*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN+P':
        alumode = 0
    elif opcode == 'A*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN+P>>17':
        alumode = 0
    elif opcode == 'A*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN+PCIN':
        alumode = 0
    elif opcode == 'A*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'A*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == 'A*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'A+C':
        alumode = 0
    elif opcode == 'A+C+CARRYIN':
        alumode = 0
    elif opcode == 'A+CARRYIN':
        alumode = 0
    elif opcode == 'A+P':
        alumode = 0
    elif opcode == 'A+P+CARRYIN':
        alumode = 0
    elif opcode == 'A+P>>17':
        alumode = 0
    elif opcode == 'A+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'A+PCIN':
        alumode = 0
    elif opcode == 'A+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'A+PCIN>>17':
        alumode = 0
    elif opcode == 'A+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN':
        alumode = 0
    elif opcode == 'ACIN*B':
        alumode = 0
    elif opcode == 'ACIN*B+C':
        alumode = 0
    elif opcode == 'ACIN*B+C+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*B+P':
        alumode = 0
    elif opcode == 'ACIN*B+P+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*B+P>>17':
        alumode = 0
    elif opcode == 'ACIN*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*B+PCIN':
        alumode = 0
    elif opcode == 'ACIN*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*B+PCIN>>17':
        alumode = 0
    elif opcode == 'ACIN*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+C':
        alumode = 0
    elif opcode == 'ACIN*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+P':
        alumode = 0
    elif opcode == 'ACIN*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+P>>17':
        alumode = 0
    elif opcode == 'ACIN*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+PCIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == 'ACIN*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+C':
        alumode = 0
    elif opcode == 'ACIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+P':
        alumode = 0
    elif opcode == 'ACIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+P>>17':
        alumode = 0
    elif opcode == 'ACIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+PCIN':
        alumode = 0
    elif opcode == 'ACIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'ACIN+PCIN>>17':
        alumode = 0
    elif opcode == 'ACIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)':
        alumode = 0
    elif opcode == 'B*(A+D)+C':
        alumode = 0
    elif opcode == 'B*(A+D)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)+P':
        alumode = 0
    elif opcode == 'B*(A+D)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)+P>>17':
        alumode = 0
    elif opcode == 'B*(A+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)+PCIN':
        alumode = 0
    elif opcode == 'B*(A+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(A+D)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(A+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+C':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+P':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+P>>17':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+PCIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(ACIN+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)':
        alumode = 0
    elif opcode == 'B*(D+A)+C':
        alumode = 0
    elif opcode == 'B*(D+A)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)+P':
        alumode = 0
    elif opcode == 'B*(D+A)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)+P>>17':
        alumode = 0
    elif opcode == 'B*(D+A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)+PCIN':
        alumode = 0
    elif opcode == 'B*(D+A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+A)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(D+A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+C':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+P':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+P>>17':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+PCIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(D+ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)':
        alumode = 0
    elif opcode == 'B*(D-A)+C':
        alumode = 0
    elif opcode == 'B*(D-A)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)+P':
        alumode = 0
    elif opcode == 'B*(D-A)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)+P>>17':
        alumode = 0
    elif opcode == 'B*(D-A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)+PCIN':
        alumode = 0
    elif opcode == 'B*(D-A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-A)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(D-A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+C':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+P':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+P>>17':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+PCIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == 'B*(D-ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*A':
        alumode = 0
    elif opcode == 'B*A+C':
        alumode = 0
    elif opcode == 'B*A+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*A+CARRYIN':
        alumode = 0
    elif opcode == 'B*A+P':
        alumode = 0
    elif opcode == 'B*A+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*A+P>>17':
        alumode = 0
    elif opcode == 'B*A+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*A+PCIN':
        alumode = 0
    elif opcode == 'B*A+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*A+PCIN>>17':
        alumode = 0
    elif opcode == 'B*A+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN':
        alumode = 0
    elif opcode == 'B*ACIN+C':
        alumode = 0
    elif opcode == 'B*ACIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN+P':
        alumode = 0
    elif opcode == 'B*ACIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN+P>>17':
        alumode = 0
    elif opcode == 'B*ACIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN+PCIN':
        alumode = 0
    elif opcode == 'B*ACIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*ACIN+PCIN>>17':
        alumode = 0
    elif opcode == 'B*ACIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*D':
        alumode = 0
    elif opcode == 'B*D+C':
        alumode = 0
    elif opcode == 'B*D+C+CARRYIN':
        alumode = 0
    elif opcode == 'B*D+CARRYIN':
        alumode = 0
    elif opcode == 'B*D+P':
        alumode = 0
    elif opcode == 'B*D+P+CARRYIN':
        alumode = 0
    elif opcode == 'B*D+P>>17':
        alumode = 0
    elif opcode == 'B*D+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'B*D+PCIN':
        alumode = 0
    elif opcode == 'B*D+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'B*D+PCIN>>17':
        alumode = 0
    elif opcode == 'B*D+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+C':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+P':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(A+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+C':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+P':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(ACIN+D)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+C':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+P':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(D+A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+C':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+P':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(D+ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+C':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+P':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(D-A)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+C':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+P':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+P>>17':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+PCIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*(D-ACIN)+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A':
        alumode = 0
    elif opcode == 'BCIN*A+C':
        alumode = 0
    elif opcode == 'BCIN*A+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A+P':
        alumode = 0
    elif opcode == 'BCIN*A+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A+P>>17':
        alumode = 0
    elif opcode == 'BCIN*A+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A+PCIN':
        alumode = 0
    elif opcode == 'BCIN*A+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*A+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*A+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+C':
        alumode = 0
    elif opcode == 'BCIN*ACIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+P':
        alumode = 0
    elif opcode == 'BCIN*ACIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+P>>17':
        alumode = 0
    elif opcode == 'BCIN*ACIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+PCIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*ACIN+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*ACIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D':
        alumode = 0
    elif opcode == 'BCIN*D+C':
        alumode = 0
    elif opcode == 'BCIN*D+C+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D+P':
        alumode = 0
    elif opcode == 'BCIN*D+P+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D+P>>17':
        alumode = 0
    elif opcode == 'BCIN*D+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D+PCIN':
        alumode = 0
    elif opcode == 'BCIN*D+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'BCIN*D+PCIN>>17':
        alumode = 0
    elif opcode == 'BCIN*D+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C':
        alumode = 0
    elif opcode == 'C+(A+D)':
        alumode = 0
    elif opcode == 'C+(A+D)*B':
        alumode = 0
    elif opcode == 'C+(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(A+D)*BCIN':
        alumode = 0
    elif opcode == 'C+(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+(ACIN+D)':
        alumode = 0
    elif opcode == 'C+(ACIN+D)*B':
        alumode = 0
    elif opcode == 'C+(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'C+(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+A)':
        alumode = 0
    elif opcode == 'C+(D+A)*B':
        alumode = 0
    elif opcode == 'C+(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+A)*BCIN':
        alumode = 0
    elif opcode == 'C+(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+ACIN)':
        alumode = 0
    elif opcode == 'C+(D+ACIN)*B':
        alumode = 0
    elif opcode == 'C+(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'C+(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-A)':
        alumode = 0
    elif opcode == 'C+(D-A)*B':
        alumode = 0
    elif opcode == 'C+(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-A)*BCIN':
        alumode = 0
    elif opcode == 'C+(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-ACIN)':
        alumode = 0
    elif opcode == 'C+(D-ACIN)*B':
        alumode = 0
    elif opcode == 'C+(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'C+(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+A':
        alumode = 0
    elif opcode == 'C+A*B':
        alumode = 0
    elif opcode == 'C+A*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+A*BCIN':
        alumode = 0
    elif opcode == 'C+A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+A+CARRYIN':
        alumode = 0
    elif opcode == 'C+ACIN':
        alumode = 0
    elif opcode == 'C+ACIN*B':
        alumode = 0
    elif opcode == 'C+ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+ACIN*BCIN':
        alumode = 0
    elif opcode == 'C+ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(A+D)':
        alumode = 0
    elif opcode == 'C+B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(ACIN+D)':
        alumode = 0
    elif opcode == 'C+B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(D+A)':
        alumode = 0
    elif opcode == 'C+B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(D+ACIN)':
        alumode = 0
    elif opcode == 'C+B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(D-A)':
        alumode = 0
    elif opcode == 'C+B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*(D-ACIN)':
        alumode = 0
    elif opcode == 'C+B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*A':
        alumode = 0
    elif opcode == 'C+B*A+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*ACIN':
        alumode = 0
    elif opcode == 'C+B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+B*D':
        alumode = 0
    elif opcode == 'C+B*D+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(A+D)':
        alumode = 0
    elif opcode == 'C+BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'C+BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(D+A)':
        alumode = 0
    elif opcode == 'C+BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'C+BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(D-A)':
        alumode = 0
    elif opcode == 'C+BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'C+BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*A':
        alumode = 0
    elif opcode == 'C+BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*ACIN':
        alumode = 0
    elif opcode == 'C+BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+BCIN*D':
        alumode = 0
    elif opcode == 'C+BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'C+C':
        alumode = 0
    elif opcode == 'C+C+CARRYCASCIN':
        alumode = 0
    elif opcode == 'C+C+CARRYIN':
        alumode = 0
    elif opcode == 'C+C+CONCAT':
        alumode = 0
    elif opcode == 'C+C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+C+P':
        alumode = 0
    elif opcode == 'C+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+CARRYCASCIN':
        alumode = 0
    elif opcode == 'C+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT':
        alumode = 0
    elif opcode == 'C+CONCAT+C':
        alumode = 0
    elif opcode == 'C+CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT+CARRYCASCIN':
        alumode = 0
    elif opcode == 'C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT+P':
        alumode = 0
    elif opcode == 'C+CONCAT+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT+P>>17':
        alumode = 0
    elif opcode == 'C+CONCAT+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT+PCIN':
        alumode = 0
    elif opcode == 'C+CONCAT+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+CONCAT+PCIN>>17':
        alumode = 0
    elif opcode == 'C+CONCAT+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+D':
        alumode = 0
    elif opcode == 'C+D*B':
        alumode = 0
    elif opcode == 'C+D*B+CARRYIN':
        alumode = 0
    elif opcode == 'C+D*BCIN':
        alumode = 0
    elif opcode == 'C+D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+D+CARRYIN':
        alumode = 0
    elif opcode == 'C+P':
        alumode = 0
    elif opcode == 'C+P+C':
        alumode = 0
    elif opcode == 'C+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+CARRYCASCIN':
        alumode = 0
    elif opcode == 'C+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+CONCAT':
        alumode = 0
    elif opcode == 'C+P+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+P':
        alumode = 0
    elif opcode == 'C+P+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+P>>17':
        alumode = 0
    elif opcode == 'C+P+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+PCIN':
        alumode = 0
    elif opcode == 'C+P+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+P+PCIN>>17':
        alumode = 0
    elif opcode == 'C+P+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+P>>17':
        alumode = 0
    elif opcode == 'C+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+P>>17+CONCAT':
        alumode = 0
    elif opcode == 'C+P>>17+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+P>>17+P':
        alumode = 0
    elif opcode == 'C+P>>17+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN':
        alumode = 0
    elif opcode == 'C+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN+CONCAT':
        alumode = 0
    elif opcode == 'C+PCIN+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN+P':
        alumode = 0
    elif opcode == 'C+PCIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN>>17':
        alumode = 0
    elif opcode == 'C+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN>>17+CONCAT':
        alumode = 0
    elif opcode == 'C+PCIN>>17+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'C+PCIN>>17+P':
        alumode = 0
    elif opcode == 'C+PCIN>>17+P+CARRYIN':
        alumode = 0
    elif opcode == 'C-((A+D))':
        alumode = 3
    elif opcode == 'C-((A+D)*B)':
        alumode = 3
    elif opcode == 'C-((A+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((A+D)*BCIN)':
        alumode = 3
    elif opcode == 'C-((A+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((ACIN+D))':
        alumode = 3
    elif opcode == 'C-((ACIN+D)*B)':
        alumode = 3
    elif opcode == 'C-((ACIN+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((ACIN+D)*BCIN)':
        alumode = 3
    elif opcode == 'C-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+A))':
        alumode = 3
    elif opcode == 'C-((D+A)*B)':
        alumode = 3
    elif opcode == 'C-((D+A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+A)*BCIN)':
        alumode = 3
    elif opcode == 'C-((D+A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+ACIN))':
        alumode = 3
    elif opcode == 'C-((D+ACIN)*B)':
        alumode = 3
    elif opcode == 'C-((D+ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'C-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-A))':
        alumode = 3
    elif opcode == 'C-((D-A)*B)':
        alumode = 3
    elif opcode == 'C-((D-A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-A)*BCIN)':
        alumode = 3
    elif opcode == 'C-((D-A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-ACIN))':
        alumode = 3
    elif opcode == 'C-((D-ACIN)*B)':
        alumode = 3
    elif opcode == 'C-((D-ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'C-((D-ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-((D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(A)':
        alumode = 3
    elif opcode == 'C-(A*B)':
        alumode = 3
    elif opcode == 'C-(A*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(A*BCIN)':
        alumode = 3
    elif opcode == 'C-(A*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(A+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(A+D)':
        alumode = 3
    elif opcode == 'C-(A+D)*B':
        alumode = 3
    elif opcode == 'C-(A+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(A+D)*BCIN':
        alumode = 3
    elif opcode == 'C-(A+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(ACIN)':
        alumode = 3
    elif opcode == 'C-(ACIN*B)':
        alumode = 3
    elif opcode == 'C-(ACIN*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(ACIN*BCIN)':
        alumode = 3
    elif opcode == 'C-(ACIN*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(ACIN+D)':
        alumode = 3
    elif opcode == 'C-(ACIN+D)*B':
        alumode = 3
    elif opcode == 'C-(ACIN+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(ACIN+D)*BCIN':
        alumode = 3
    elif opcode == 'C-(ACIN+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(B*(A+D))':
        alumode = 3
    elif opcode == 'C-(B*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*(ACIN+D))':
        alumode = 3
    elif opcode == 'C-(B*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*(D+A))':
        alumode = 3
    elif opcode == 'C-(B*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*(D+ACIN))':
        alumode = 3
    elif opcode == 'C-(B*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*(D-A))':
        alumode = 3
    elif opcode == 'C-(B*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*(D-ACIN))':
        alumode = 3
    elif opcode == 'C-(B*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*A)':
        alumode = 3
    elif opcode == 'C-(B*A+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*ACIN)':
        alumode = 3
    elif opcode == 'C-(B*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(B*D)':
        alumode = 3
    elif opcode == 'C-(B*D+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(A+D))':
        alumode = 3
    elif opcode == 'C-(BCIN*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(ACIN+D))':
        alumode = 3
    elif opcode == 'C-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(D+A))':
        alumode = 3
    elif opcode == 'C-(BCIN*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(D+ACIN))':
        alumode = 3
    elif opcode == 'C-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(D-A))':
        alumode = 3
    elif opcode == 'C-(BCIN*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*(D-ACIN))':
        alumode = 3
    elif opcode == 'C-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*A)':
        alumode = 3
    elif opcode == 'C-(BCIN*A+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*ACIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(BCIN*D)':
        alumode = 3
    elif opcode == 'C-(BCIN*D+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(C)':
        alumode = 3
    elif opcode == 'C-(C+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'C-(C+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(C+CONCAT)':
        alumode = 3
    elif opcode == 'C-(C+CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(C+P)':
        alumode = 3
    elif opcode == 'C-(C+P+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(CARRYCASCIN)':
        alumode = 3
    elif opcode == 'C-(CARRYIN)':
        alumode = 3
    elif opcode == 'C-(CONCAT)':
        alumode = 3
    elif opcode == 'C-(CONCAT+C)':
        alumode = 3
    elif opcode == 'C-(CONCAT+C+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(CONCAT+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'C-(CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(D)':
        alumode = 3
    elif opcode == 'C-(D*B)':
        alumode = 3
    elif opcode == 'C-(D*B+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(D*BCIN)':
        alumode = 3
    elif opcode == 'C-(D*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(D+A)':
        alumode = 3
    elif opcode == 'C-(D+A)*B':
        alumode = 3
    elif opcode == 'C-(D+A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+A)*BCIN':
        alumode = 3
    elif opcode == 'C-(D+A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+ACIN)':
        alumode = 3
    elif opcode == 'C-(D+ACIN)*B':
        alumode = 3
    elif opcode == 'C-(D+ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+ACIN)*BCIN':
        alumode = 3
    elif opcode == 'C-(D+ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(D-A)':
        alumode = 3
    elif opcode == 'C-(D-A)*B':
        alumode = 3
    elif opcode == 'C-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D-A)*BCIN':
        alumode = 3
    elif opcode == 'C-(D-A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D-ACIN)':
        alumode = 3
    elif opcode == 'C-(D-ACIN)*B':
        alumode = 3
    elif opcode == 'C-(D-ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D-ACIN)*BCIN':
        alumode = 3
    elif opcode == 'C-(D-ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-(P)':
        alumode = 3
    elif opcode == 'C-(P+C)':
        alumode = 3
    elif opcode == 'C-(P+C+CARRYIN)':
        alumode = 3
    elif opcode == 'C-(P+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'C-(P+CARRYIN)':
        alumode = 3
    elif opcode == 'C-A':
        alumode = 3
    elif opcode == 'C-A*B':
        alumode = 3
    elif opcode == 'C-A*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-A*BCIN':
        alumode = 3
    elif opcode == 'C-A*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-A-CARRYIN':
        alumode = 3
    elif opcode == 'C-ACIN':
        alumode = 3
    elif opcode == 'C-ACIN*B':
        alumode = 3
    elif opcode == 'C-ACIN*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-ACIN*BCIN':
        alumode = 3
    elif opcode == 'C-ACIN*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(A+D)':
        alumode = 3
    elif opcode == 'C-B*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(ACIN+D)':
        alumode = 3
    elif opcode == 'C-B*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(D+A)':
        alumode = 3
    elif opcode == 'C-B*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(D+ACIN)':
        alumode = 3
    elif opcode == 'C-B*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(D-A)':
        alumode = 3
    elif opcode == 'C-B*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*(D-ACIN)':
        alumode = 3
    elif opcode == 'C-B*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*A':
        alumode = 3
    elif opcode == 'C-B*A-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*ACIN':
        alumode = 3
    elif opcode == 'C-B*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-B*D':
        alumode = 3
    elif opcode == 'C-B*D-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(A+D)':
        alumode = 3
    elif opcode == 'C-BCIN*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(ACIN+D)':
        alumode = 3
    elif opcode == 'C-BCIN*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(D+A)':
        alumode = 3
    elif opcode == 'C-BCIN*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(D+ACIN)':
        alumode = 3
    elif opcode == 'C-BCIN*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(D-A)':
        alumode = 3
    elif opcode == 'C-BCIN*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*(D-ACIN)':
        alumode = 3
    elif opcode == 'C-BCIN*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*A':
        alumode = 3
    elif opcode == 'C-BCIN*A-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*ACIN':
        alumode = 3
    elif opcode == 'C-BCIN*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-BCIN*D':
        alumode = 3
    elif opcode == 'C-BCIN*D-CARRYIN':
        alumode = 3
    elif opcode == 'C-C':
        alumode = 3
    elif opcode == 'C-C-CARRYCASCIN':
        alumode = 3
    elif opcode == 'C-C-CARRYIN':
        alumode = 3
    elif opcode == 'C-C-CONCAT':
        alumode = 3
    elif opcode == 'C-C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'C-C-P':
        alumode = 3
    elif opcode == 'C-C-P-CARRYIN':
        alumode = 3
    elif opcode == 'C-CARRYCASCIN':
        alumode = 3
    elif opcode == 'C-CARRYIN':
        alumode = 3
    elif opcode == 'C-CONCAT':
        alumode = 3
    elif opcode == 'C-CONCAT-C':
        alumode = 3
    elif opcode == 'C-CONCAT-C-CARRYIN':
        alumode = 3
    elif opcode == 'C-CONCAT-CARRYCASCIN':
        alumode = 3
    elif opcode == 'C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'C-D':
        alumode = 3
    elif opcode == 'C-D*B':
        alumode = 3
    elif opcode == 'C-D*B-CARRYIN':
        alumode = 3
    elif opcode == 'C-D*BCIN':
        alumode = 3
    elif opcode == 'C-D*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'C-D-CARRYIN':
        alumode = 3
    elif opcode == 'C-P':
        alumode = 3
    elif opcode == 'C-P-C':
        alumode = 3
    elif opcode == 'C-P-C-CARRYIN':
        alumode = 3
    elif opcode == 'C-P-CARRYCASCIN':
        alumode = 3
    elif opcode == 'C-P-CARRYIN':
        alumode = 3
    elif opcode == 'CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT':
        alumode = 0
    elif opcode == 'CONCAT+C':
        alumode = 0
    elif opcode == 'CONCAT+C+C':
        alumode = 0
    elif opcode == 'CONCAT+C+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+C+CARRYCASCIN':
        alumode = 0
    elif opcode == 'CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+C+P':
        alumode = 0
    elif opcode == 'CONCAT+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+C+P>>17':
        alumode = 0
    elif opcode == 'CONCAT+C+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+C+PCIN':
        alumode = 0
    elif opcode == 'CONCAT+C+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+C+PCIN>>17':
        alumode = 0
    elif opcode == 'CONCAT+C+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+CARRYCASCIN':
        alumode = 0
    elif opcode == 'CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+P':
        alumode = 0
    elif opcode == 'CONCAT+P+C':
        alumode = 0
    elif opcode == 'CONCAT+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+P+CARRYCASCIN':
        alumode = 0
    elif opcode == 'CONCAT+P+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+P>>17':
        alumode = 0
    elif opcode == 'CONCAT+P>>17+C':
        alumode = 0
    elif opcode == 'CONCAT+P>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+PCIN':
        alumode = 0
    elif opcode == 'CONCAT+PCIN+C':
        alumode = 0
    elif opcode == 'CONCAT+PCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+PCIN>>17':
        alumode = 0
    elif opcode == 'CONCAT+PCIN>>17+C':
        alumode = 0
    elif opcode == 'CONCAT+PCIN>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'CONCAT+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D':
        alumode = 0
    elif opcode == 'D*B':
        alumode = 0
    elif opcode == 'D*B+C':
        alumode = 0
    elif opcode == 'D*B+C+CARRYIN':
        alumode = 0
    elif opcode == 'D*B+CARRYIN':
        alumode = 0
    elif opcode == 'D*B+P':
        alumode = 0
    elif opcode == 'D*B+P+CARRYIN':
        alumode = 0
    elif opcode == 'D*B+P>>17':
        alumode = 0
    elif opcode == 'D*B+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D*B+PCIN':
        alumode = 0
    elif opcode == 'D*B+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'D*B+PCIN>>17':
        alumode = 0
    elif opcode == 'D*B+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN':
        alumode = 0
    elif opcode == 'D*BCIN+C':
        alumode = 0
    elif opcode == 'D*BCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN+P':
        alumode = 0
    elif opcode == 'D*BCIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN+P>>17':
        alumode = 0
    elif opcode == 'D*BCIN+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN+PCIN':
        alumode = 0
    elif opcode == 'D*BCIN+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'D*BCIN+PCIN>>17':
        alumode = 0
    elif opcode == 'D*BCIN+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D+C':
        alumode = 0
    elif opcode == 'D+C+CARRYIN':
        alumode = 0
    elif opcode == 'D+CARRYIN':
        alumode = 0
    elif opcode == 'D+P':
        alumode = 0
    elif opcode == 'D+P+CARRYIN':
        alumode = 0
    elif opcode == 'D+P>>17':
        alumode = 0
    elif opcode == 'D+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'D+PCIN':
        alumode = 0
    elif opcode == 'D+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'D+PCIN>>17':
        alumode = 0
    elif opcode == 'D+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P':
        alumode = 0
    elif opcode == 'P+(A+D)':
        alumode = 0
    elif opcode == 'P+(A+D)*B':
        alumode = 0
    elif opcode == 'P+(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(A+D)*BCIN':
        alumode = 0
    elif opcode == 'P+(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+(ACIN+D)':
        alumode = 0
    elif opcode == 'P+(ACIN+D)*B':
        alumode = 0
    elif opcode == 'P+(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'P+(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+A)':
        alumode = 0
    elif opcode == 'P+(D+A)*B':
        alumode = 0
    elif opcode == 'P+(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+A)*BCIN':
        alumode = 0
    elif opcode == 'P+(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+ACIN)':
        alumode = 0
    elif opcode == 'P+(D+ACIN)*B':
        alumode = 0
    elif opcode == 'P+(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P+(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-A)':
        alumode = 0
    elif opcode == 'P+(D-A)*B':
        alumode = 0
    elif opcode == 'P+(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-A)*BCIN':
        alumode = 0
    elif opcode == 'P+(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-ACIN)':
        alumode = 0
    elif opcode == 'P+(D-ACIN)*B':
        alumode = 0
    elif opcode == 'P+(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P+(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+A':
        alumode = 0
    elif opcode == 'P+A*B':
        alumode = 0
    elif opcode == 'P+A*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+A*BCIN':
        alumode = 0
    elif opcode == 'P+A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+A+CARRYIN':
        alumode = 0
    elif opcode == 'P+ACIN':
        alumode = 0
    elif opcode == 'P+ACIN*B':
        alumode = 0
    elif opcode == 'P+ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+ACIN*BCIN':
        alumode = 0
    elif opcode == 'P+ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(A+D)':
        alumode = 0
    elif opcode == 'P+B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(ACIN+D)':
        alumode = 0
    elif opcode == 'P+B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(D+A)':
        alumode = 0
    elif opcode == 'P+B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(D+ACIN)':
        alumode = 0
    elif opcode == 'P+B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(D-A)':
        alumode = 0
    elif opcode == 'P+B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*(D-ACIN)':
        alumode = 0
    elif opcode == 'P+B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*A':
        alumode = 0
    elif opcode == 'P+B*A+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*ACIN':
        alumode = 0
    elif opcode == 'P+B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+B*D':
        alumode = 0
    elif opcode == 'P+B*D+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(A+D)':
        alumode = 0
    elif opcode == 'P+BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'P+BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(D+A)':
        alumode = 0
    elif opcode == 'P+BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'P+BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(D-A)':
        alumode = 0
    elif opcode == 'P+BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'P+BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*A':
        alumode = 0
    elif opcode == 'P+BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*ACIN':
        alumode = 0
    elif opcode == 'P+BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+BCIN*D':
        alumode = 0
    elif opcode == 'P+BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'P+C':
        alumode = 0
    elif opcode == 'P+C+C':
        alumode = 0
    elif opcode == 'P+C+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+CARRYCASCIN':
        alumode = 0
    elif opcode == 'P+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+CONCAT':
        alumode = 0
    elif opcode == 'P+C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+P':
        alumode = 0
    elif opcode == 'P+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+P>>17':
        alumode = 0
    elif opcode == 'P+C+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+PCIN':
        alumode = 0
    elif opcode == 'P+C+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+C+PCIN>>17':
        alumode = 0
    elif opcode == 'P+C+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P+CARRYCASCIN':
        alumode = 0
    elif opcode == 'P+CARRYIN':
        alumode = 0
    elif opcode == 'P+CONCAT':
        alumode = 0
    elif opcode == 'P+CONCAT+C':
        alumode = 0
    elif opcode == 'P+CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+CONCAT+CARRYCASCIN':
        alumode = 0
    elif opcode == 'P+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'P+D':
        alumode = 0
    elif opcode == 'P+D*B':
        alumode = 0
    elif opcode == 'P+D*B+CARRYIN':
        alumode = 0
    elif opcode == 'P+D*BCIN':
        alumode = 0
    elif opcode == 'P+D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+D+CARRYIN':
        alumode = 0
    elif opcode == 'P+P':
        alumode = 0
    elif opcode == 'P+P+C':
        alumode = 0
    elif opcode == 'P+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+P+CARRYCASCIN':
        alumode = 0
    elif opcode == 'P+P+CARRYIN':
        alumode = 0
    elif opcode == 'P+P>>17':
        alumode = 0
    elif opcode == 'P+P>>17+C':
        alumode = 0
    elif opcode == 'P+P>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P+PCIN':
        alumode = 0
    elif opcode == 'P+PCIN+C':
        alumode = 0
    elif opcode == 'P+PCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P+PCIN>>17':
        alumode = 0
    elif opcode == 'P+PCIN>>17+C':
        alumode = 0
    elif opcode == 'P+PCIN>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'P+PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P-((A+D))':
        alumode = 3
    elif opcode == 'P-((A+D)*B)':
        alumode = 3
    elif opcode == 'P-((A+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((A+D)*BCIN)':
        alumode = 3
    elif opcode == 'P-((A+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((ACIN+D))':
        alumode = 3
    elif opcode == 'P-((ACIN+D)*B)':
        alumode = 3
    elif opcode == 'P-((ACIN+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((ACIN+D)*BCIN)':
        alumode = 3
    elif opcode == 'P-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+A))':
        alumode = 3
    elif opcode == 'P-((D+A)*B)':
        alumode = 3
    elif opcode == 'P-((D+A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+A)*BCIN)':
        alumode = 3
    elif opcode == 'P-((D+A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+ACIN))':
        alumode = 3
    elif opcode == 'P-((D+ACIN)*B)':
        alumode = 3
    elif opcode == 'P-((D+ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'P-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-A))':
        alumode = 3
    elif opcode == 'P-((D-A)*B)':
        alumode = 3
    elif opcode == 'P-((D-A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-A)*BCIN)':
        alumode = 3
    elif opcode == 'P-((D-A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-ACIN))':
        alumode = 3
    elif opcode == 'P-((D-ACIN)*B)':
        alumode = 3
    elif opcode == 'P-((D-ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'P-((D-ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-((D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(A)':
        alumode = 3
    elif opcode == 'P-(A*B)':
        alumode = 3
    elif opcode == 'P-(A*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(A*BCIN)':
        alumode = 3
    elif opcode == 'P-(A*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(A+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(A+D)':
        alumode = 3
    elif opcode == 'P-(A+D)*B':
        alumode = 3
    elif opcode == 'P-(A+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(A+D)*BCIN':
        alumode = 3
    elif opcode == 'P-(A+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(ACIN)':
        alumode = 3
    elif opcode == 'P-(ACIN*B)':
        alumode = 3
    elif opcode == 'P-(ACIN*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(ACIN*BCIN)':
        alumode = 3
    elif opcode == 'P-(ACIN*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(ACIN+D)':
        alumode = 3
    elif opcode == 'P-(ACIN+D)*B':
        alumode = 3
    elif opcode == 'P-(ACIN+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(ACIN+D)*BCIN':
        alumode = 3
    elif opcode == 'P-(ACIN+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(B*(A+D))':
        alumode = 3
    elif opcode == 'P-(B*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*(ACIN+D))':
        alumode = 3
    elif opcode == 'P-(B*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*(D+A))':
        alumode = 3
    elif opcode == 'P-(B*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*(D+ACIN))':
        alumode = 3
    elif opcode == 'P-(B*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*(D-A))':
        alumode = 3
    elif opcode == 'P-(B*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*(D-ACIN))':
        alumode = 3
    elif opcode == 'P-(B*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*A)':
        alumode = 3
    elif opcode == 'P-(B*A+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*ACIN)':
        alumode = 3
    elif opcode == 'P-(B*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(B*D)':
        alumode = 3
    elif opcode == 'P-(B*D+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(A+D))':
        alumode = 3
    elif opcode == 'P-(BCIN*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(ACIN+D))':
        alumode = 3
    elif opcode == 'P-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(D+A))':
        alumode = 3
    elif opcode == 'P-(BCIN*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(D+ACIN))':
        alumode = 3
    elif opcode == 'P-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(D-A))':
        alumode = 3
    elif opcode == 'P-(BCIN*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*(D-ACIN))':
        alumode = 3
    elif opcode == 'P-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*A)':
        alumode = 3
    elif opcode == 'P-(BCIN*A+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*ACIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(BCIN*D)':
        alumode = 3
    elif opcode == 'P-(BCIN*D+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(C)':
        alumode = 3
    elif opcode == 'P-(C+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'P-(C+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(C+CONCAT)':
        alumode = 3
    elif opcode == 'P-(C+CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(C+P)':
        alumode = 3
    elif opcode == 'P-(C+P+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(CARRYCASCIN)':
        alumode = 3
    elif opcode == 'P-(CARRYIN)':
        alumode = 3
    elif opcode == 'P-(CONCAT)':
        alumode = 3
    elif opcode == 'P-(CONCAT+C)':
        alumode = 3
    elif opcode == 'P-(CONCAT+C+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(CONCAT+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'P-(CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(D)':
        alumode = 3
    elif opcode == 'P-(D*B)':
        alumode = 3
    elif opcode == 'P-(D*B+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(D*BCIN)':
        alumode = 3
    elif opcode == 'P-(D*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(D+A)':
        alumode = 3
    elif opcode == 'P-(D+A)*B':
        alumode = 3
    elif opcode == 'P-(D+A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+A)*BCIN':
        alumode = 3
    elif opcode == 'P-(D+A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+ACIN)':
        alumode = 3
    elif opcode == 'P-(D+ACIN)*B':
        alumode = 3
    elif opcode == 'P-(D+ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+ACIN)*BCIN':
        alumode = 3
    elif opcode == 'P-(D+ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(D-A)':
        alumode = 3
    elif opcode == 'P-(D-A)*B':
        alumode = 3
    elif opcode == 'P-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D-A)*BCIN':
        alumode = 3
    elif opcode == 'P-(D-A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D-ACIN)':
        alumode = 3
    elif opcode == 'P-(D-ACIN)*B':
        alumode = 3
    elif opcode == 'P-(D-ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D-ACIN)*BCIN':
        alumode = 3
    elif opcode == 'P-(D-ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-(P)':
        alumode = 3
    elif opcode == 'P-(P+C)':
        alumode = 3
    elif opcode == 'P-(P+C+CARRYIN)':
        alumode = 3
    elif opcode == 'P-(P+CARRYCASCIN)':
        alumode = 3
    elif opcode == 'P-(P+CARRYIN)':
        alumode = 3
    elif opcode == 'P-A':
        alumode = 3
    elif opcode == 'P-A*B':
        alumode = 3
    elif opcode == 'P-A*B-CARRYIN':
        alumode = 3
        inmode_diff = -1
    elif opcode == 'P-A*BCIN':
        alumode = 3
    elif opcode == 'P-A*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-A-CARRYIN':
        alumode = 3
    elif opcode == 'P-ACIN':
        alumode = 3
    elif opcode == 'P-ACIN*B':
        alumode = 3
    elif opcode == 'P-ACIN*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-ACIN*BCIN':
        alumode = 3
    elif opcode == 'P-ACIN*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(A+D)':
        alumode = 3
    elif opcode == 'P-B*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(ACIN+D)':
        alumode = 3
    elif opcode == 'P-B*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(D+A)':
        alumode = 3
    elif opcode == 'P-B*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(D+ACIN)':
        alumode = 3
    elif opcode == 'P-B*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(D-A)':
        alumode = 3
    elif opcode == 'P-B*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*(D-ACIN)':
        alumode = 3
    elif opcode == 'P-B*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*A':
        alumode = 3
    elif opcode == 'P-B*A-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*ACIN':
        alumode = 3
    elif opcode == 'P-B*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-B*D':
        alumode = 3
    elif opcode == 'P-B*D-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(A+D)':
        alumode = 3
    elif opcode == 'P-BCIN*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(ACIN+D)':
        alumode = 3
    elif opcode == 'P-BCIN*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(D+A)':
        alumode = 3
    elif opcode == 'P-BCIN*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(D+ACIN)':
        alumode = 3
    elif opcode == 'P-BCIN*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(D-A)':
        alumode = 3
    elif opcode == 'P-BCIN*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*(D-ACIN)':
        alumode = 3
    elif opcode == 'P-BCIN*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*A':
        alumode = 3
    elif opcode == 'P-BCIN*A-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*ACIN':
        alumode = 3
    elif opcode == 'P-BCIN*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-BCIN*D':
        alumode = 3
    elif opcode == 'P-BCIN*D-CARRYIN':
        alumode = 3
    elif opcode == 'P-C':
        alumode = 3
    elif opcode == 'P-C-CARRYCASCIN':
        alumode = 3
    elif opcode == 'P-C-CARRYIN':
        alumode = 3
    elif opcode == 'P-C-CONCAT':
        alumode = 3
    elif opcode == 'P-C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'P-C-P':
        alumode = 3
    elif opcode == 'P-C-P-CARRYIN':
        alumode = 3
    elif opcode == 'P-CARRYCASCIN':
        alumode = 3
    elif opcode == 'P-CARRYIN':
        alumode = 3
    elif opcode == 'P-CONCAT':
        alumode = 3
    elif opcode == 'P-CONCAT-C':
        alumode = 3
    elif opcode == 'P-CONCAT-C-CARRYIN':
        alumode = 3
    elif opcode == 'P-CONCAT-CARRYCASCIN':
        alumode = 3
    elif opcode == 'P-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'P-D':
        alumode = 3
    elif opcode == 'P-D*B':
        alumode = 3
    elif opcode == 'P-D*B-CARRYIN':
        alumode = 3
    elif opcode == 'P-D*BCIN':
        alumode = 3
    elif opcode == 'P-D*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'P-D-CARRYIN':
        alumode = 3
    elif opcode == 'P-P':
        alumode = 3
    elif opcode == 'P-P-C':
        alumode = 3
    elif opcode == 'P-P-C-CARRYIN':
        alumode = 3
    elif opcode == 'P-P-CARRYCASCIN':
        alumode = 3
    elif opcode == 'P-P-CARRYIN':
        alumode = 3
    elif opcode == 'P>>17':
        alumode = 0
    elif opcode == 'P>>17+(A+D)':
        alumode = 0
    elif opcode == 'P>>17+(A+D)*B':
        alumode = 0
    elif opcode == 'P>>17+(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(A+D)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)*B':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+A)':
        alumode = 0
    elif opcode == 'P>>17+(D+A)*B':
        alumode = 0
    elif opcode == 'P>>17+(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+A)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)*B':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-A)':
        alumode = 0
    elif opcode == 'P>>17+(D-A)*B':
        alumode = 0
    elif opcode == 'P>>17+(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-A)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)*B':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+A':
        alumode = 0
    elif opcode == 'P>>17+A*B':
        alumode = 0
    elif opcode == 'P>>17+A*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+A*BCIN':
        alumode = 0
    elif opcode == 'P>>17+A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+A+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+ACIN':
        alumode = 0
    elif opcode == 'P>>17+ACIN*B':
        alumode = 0
    elif opcode == 'P>>17+ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+ACIN*BCIN':
        alumode = 0
    elif opcode == 'P>>17+ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(A+D)':
        alumode = 0
    elif opcode == 'P>>17+B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17+B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(D+A)':
        alumode = 0
    elif opcode == 'P>>17+B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17+B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(D-A)':
        alumode = 0
    elif opcode == 'P>>17+B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17+B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*A':
        alumode = 0
    elif opcode == 'P>>17+B*A+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*ACIN':
        alumode = 0
    elif opcode == 'P>>17+B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+B*D':
        alumode = 0
    elif opcode == 'P>>17+B*D+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(A+D)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D+A)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D-A)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17+BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*A':
        alumode = 0
    elif opcode == 'P>>17+BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*ACIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+BCIN*D':
        alumode = 0
    elif opcode == 'P>>17+BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+C':
        alumode = 0
    elif opcode == 'P>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+C+CONCAT':
        alumode = 0
    elif opcode == 'P>>17+C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+C+P':
        alumode = 0
    elif opcode == 'P>>17+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+CONCAT':
        alumode = 0
    elif opcode == 'P>>17+CONCAT+C':
        alumode = 0
    elif opcode == 'P>>17+CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+D':
        alumode = 0
    elif opcode == 'P>>17+D*B':
        alumode = 0
    elif opcode == 'P>>17+D*B+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+D*BCIN':
        alumode = 0
    elif opcode == 'P>>17+D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+D+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+P':
        alumode = 0
    elif opcode == 'P>>17+P+C':
        alumode = 0
    elif opcode == 'P>>17+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17+P+CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-((A+D))':
        alumode = 0
    elif opcode == 'P>>17-((A+D)*B)':
        alumode = 0
    elif opcode == 'P>>17-((A+D)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((A+D)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((A+D)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D))':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D)*B)':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+A))':
        alumode = 0
    elif opcode == 'P>>17-((D+A)*B)':
        alumode = 0
    elif opcode == 'P>>17-((D+A)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+A)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+A)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN))':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN)*B)':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-A))':
        alumode = 0
    elif opcode == 'P>>17-((D-A)*B)':
        alumode = 0
    elif opcode == 'P>>17-((D-A)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-A)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-A)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN))':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN)*B)':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-((D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(A)':
        alumode = 0
    elif opcode == 'P>>17-(A*B)':
        alumode = 0
    elif opcode == 'P>>17-(A*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(A*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-(A*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(A+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(A+D)':
        alumode = 0
    elif opcode == 'P>>17-(A+D)*B':
        alumode = 0
    elif opcode == 'P>>17-(A+D)*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(A+D)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(A+D)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(A+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(ACIN)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN*B)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)*B':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(ACIN+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(B*(A+D))':
        alumode = 0
    elif opcode == 'P>>17-(B*(A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*(ACIN+D))':
        alumode = 0
    elif opcode == 'P>>17-(B*(ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*(D+A))':
        alumode = 0
    elif opcode == 'P>>17-(B*(D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*(D+ACIN))':
        alumode = 0
    elif opcode == 'P>>17-(B*(D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*(D-A))':
        alumode = 0
    elif opcode == 'P>>17-(B*(D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*(D-ACIN))':
        alumode = 0
    elif opcode == 'P>>17-(B*(D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*A)':
        alumode = 0
    elif opcode == 'P>>17-(B*A+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*ACIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(B*D)':
        alumode = 0
    elif opcode == 'P>>17-(B*D+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(A+D))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(ACIN+D))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D+A))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D+ACIN))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D-A))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D-ACIN))':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*A)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*A+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*ACIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*D)':
        alumode = 0
    elif opcode == 'P>>17-(BCIN*D+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(C)':
        alumode = 0
    elif opcode == 'P>>17-(C+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(C+CONCAT)':
        alumode = 0
    elif opcode == 'P>>17-(C+CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(C+P)':
        alumode = 0
    elif opcode == 'P>>17-(C+P+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(CONCAT)':
        alumode = 0
    elif opcode == 'P>>17-(CONCAT+C)':
        alumode = 0
    elif opcode == 'P>>17-(CONCAT+C+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(D)':
        alumode = 0
    elif opcode == 'P>>17-(D*B)':
        alumode = 0
    elif opcode == 'P>>17-(D*B+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(D*BCIN)':
        alumode = 0
    elif opcode == 'P>>17-(D*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(D+A)':
        alumode = 0
    elif opcode == 'P>>17-(D+A)*B':
        alumode = 0
    elif opcode == 'P>>17-(D+A)*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+A)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(D+A)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)*B':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(D-A)':
        alumode = 0
    elif opcode == 'P>>17-(D-A)*B':
        alumode = 0
    elif opcode == 'P>>17-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'P>>17-(D-A)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(D-A)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D-A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)*B':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(D-ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-(P)':
        alumode = 0
    elif opcode == 'P>>17-(P+C)':
        alumode = 0
    elif opcode == 'P>>17-(P+C+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-(P+CARRYIN)':
        alumode = 0
    elif opcode == 'P>>17-A':
        alumode = 0
    elif opcode == 'P>>17-A*B':
        alumode = 0
    elif opcode == 'P>>17-A*B-CARRYIN':
        alumode = 0
        inmode_diff = -1
    elif opcode == 'P>>17-A*BCIN':
        alumode = 0
    elif opcode == 'P>>17-A*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-A-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-ACIN':
        alumode = 0
    elif opcode == 'P>>17-ACIN*B':
        alumode = 0
    elif opcode == 'P>>17-ACIN*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-ACIN*BCIN':
        alumode = 0
    elif opcode == 'P>>17-ACIN*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-ACIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(A+D)':
        alumode = 0
    elif opcode == 'P>>17-B*(A+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17-B*(ACIN+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(D+A)':
        alumode = 0
    elif opcode == 'P>>17-B*(D+A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17-B*(D+ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(D-A)':
        alumode = 0
    elif opcode == 'P>>17-B*(D-A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17-B*(D-ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*A':
        alumode = 0
    elif opcode == 'P>>17-B*A-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*ACIN':
        alumode = 0
    elif opcode == 'P>>17-B*ACIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-B*D':
        alumode = 0
    elif opcode == 'P>>17-B*D-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(A+D)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(A+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(ACIN+D)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D+A)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D+A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D+ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D-A)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D-A)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'P>>17-BCIN*(D-ACIN)-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*A':
        alumode = 0
    elif opcode == 'P>>17-BCIN*A-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*ACIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*ACIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-BCIN*D':
        alumode = 0
    elif opcode == 'P>>17-BCIN*D-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-C':
        alumode = 0
    elif opcode == 'P>>17-C-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-C-CONCAT':
        alumode = 0
    elif opcode == 'P>>17-C-CONCAT-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-C-P':
        alumode = 0
    elif opcode == 'P>>17-C-P-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-CONCAT':
        alumode = 0
    elif opcode == 'P>>17-CONCAT-C':
        alumode = 0
    elif opcode == 'P>>17-CONCAT-C-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-CONCAT-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-D':
        alumode = 0
    elif opcode == 'P>>17-D*B':
        alumode = 0
    elif opcode == 'P>>17-D*B-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-D*BCIN':
        alumode = 0
    elif opcode == 'P>>17-D*BCIN-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-D-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-P':
        alumode = 0
    elif opcode == 'P>>17-P-C':
        alumode = 0
    elif opcode == 'P>>17-P-C-CARRYIN':
        alumode = 0
    elif opcode == 'P>>17-P-CARRYIN':
        alumode = 0
    elif opcode == 'PCIN':
        alumode = 0
    elif opcode == 'PCIN+(A+D)':
        alumode = 0
    elif opcode == 'PCIN+(A+D)*B':
        alumode = 0
    elif opcode == 'PCIN+(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(A+D)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)*B':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+A)':
        alumode = 0
    elif opcode == 'PCIN+(D+A)*B':
        alumode = 0
    elif opcode == 'PCIN+(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+A)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)*B':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-A)':
        alumode = 0
    elif opcode == 'PCIN+(D-A)*B':
        alumode = 0
    elif opcode == 'PCIN+(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-A)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)*B':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+A':
        alumode = 0
    elif opcode == 'PCIN+A*B':
        alumode = 0
    elif opcode == 'PCIN+A*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+A*BCIN':
        alumode = 0
    elif opcode == 'PCIN+A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+ACIN':
        alumode = 0
    elif opcode == 'PCIN+ACIN*B':
        alumode = 0
    elif opcode == 'PCIN+ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+ACIN*BCIN':
        alumode = 0
    elif opcode == 'PCIN+ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(A+D)':
        alumode = 0
    elif opcode == 'PCIN+B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN+B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(D+A)':
        alumode = 0
    elif opcode == 'PCIN+B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN+B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(D-A)':
        alumode = 0
    elif opcode == 'PCIN+B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN+B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*A':
        alumode = 0
    elif opcode == 'PCIN+B*A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*ACIN':
        alumode = 0
    elif opcode == 'PCIN+B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+B*D':
        alumode = 0
    elif opcode == 'PCIN+B*D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(A+D)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D+A)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D-A)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN+BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*A':
        alumode = 0
    elif opcode == 'PCIN+BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*ACIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+BCIN*D':
        alumode = 0
    elif opcode == 'PCIN+BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+C':
        alumode = 0
    elif opcode == 'PCIN+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+C+CONCAT':
        alumode = 0
    elif opcode == 'PCIN+C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+C+P':
        alumode = 0
    elif opcode == 'PCIN+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+CONCAT':
        alumode = 0
    elif opcode == 'PCIN+CONCAT+C':
        alumode = 0
    elif opcode == 'PCIN+CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+D':
        alumode = 0
    elif opcode == 'PCIN+D*B':
        alumode = 0
    elif opcode == 'PCIN+D*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+D*BCIN':
        alumode = 0
    elif opcode == 'PCIN+D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+P':
        alumode = 0
    elif opcode == 'PCIN+P+C':
        alumode = 0
    elif opcode == 'PCIN+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN+P+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN-((A+D))':
        alumode = 3
    elif opcode == 'PCIN-((A+D)*B)':
        alumode = 3
    elif opcode == 'PCIN-((A+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((A+D)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((A+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D)*B)':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+A))':
        alumode = 3
    elif opcode == 'PCIN-((D+A)*B)':
        alumode = 3
    elif opcode == 'PCIN-((D+A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+A)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN)*B)':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-A))':
        alumode = 3
    elif opcode == 'PCIN-((D-A)*B)':
        alumode = 3
    elif opcode == 'PCIN-((D-A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-A)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN)*B)':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-((D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(A)':
        alumode = 3
    elif opcode == 'PCIN-(A*B)':
        alumode = 3
    elif opcode == 'PCIN-(A*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(A*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-(A*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(A+D)':
        alumode = 3
    elif opcode == 'PCIN-(A+D)*B':
        alumode = 3
    elif opcode == 'PCIN-(A+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(A+D)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(A+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(ACIN)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN*B)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)*B':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(B*(A+D))':
        alumode = 3
    elif opcode == 'PCIN-(B*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*(ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN-(B*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*(D+A))':
        alumode = 3
    elif opcode == 'PCIN-(B*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*(D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN-(B*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*(D-A))':
        alumode = 3
    elif opcode == 'PCIN-(B*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*(D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN-(B*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*A)':
        alumode = 3
    elif opcode == 'PCIN-(B*A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*ACIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(B*D)':
        alumode = 3
    elif opcode == 'PCIN-(B*D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(A+D))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D+A))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D-A))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*A)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*ACIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*D)':
        alumode = 3
    elif opcode == 'PCIN-(BCIN*D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(C)':
        alumode = 3
    elif opcode == 'PCIN-(C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(C+CONCAT)':
        alumode = 3
    elif opcode == 'PCIN-(C+CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(C+P)':
        alumode = 3
    elif opcode == 'PCIN-(C+P+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(CONCAT)':
        alumode = 3
    elif opcode == 'PCIN-(CONCAT+C)':
        alumode = 3
    elif opcode == 'PCIN-(CONCAT+C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(D)':
        alumode = 3
    elif opcode == 'PCIN-(D*B)':
        alumode = 3
    elif opcode == 'PCIN-(D*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(D*BCIN)':
        alumode = 3
    elif opcode == 'PCIN-(D*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(D+A)':
        alumode = 3
    elif opcode == 'PCIN-(D+A)*B':
        alumode = 3
    elif opcode == 'PCIN-(D+A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+A)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(D+A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)*B':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(D-A)':
        alumode = 3
    elif opcode == 'PCIN-(D-A)*B':
        alumode = 3
    elif opcode == 'PCIN-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D-A)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(D-A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)*B':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)*BCIN':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-(P)':
        alumode = 3
    elif opcode == 'PCIN-(P+C)':
        alumode = 3
    elif opcode == 'PCIN-(P+C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-(P+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN-A':
        alumode = 3
    elif opcode == 'PCIN-A*B':
        alumode = 3
    elif opcode == 'PCIN-A*B-CARRYIN':
        alumode = 3
        inmode_diff = -1
    elif opcode == 'PCIN-A*BCIN':
        alumode = 3
    elif opcode == 'PCIN-A*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-A-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-ACIN':
        alumode = 3
    elif opcode == 'PCIN-ACIN*B':
        alumode = 3
    elif opcode == 'PCIN-ACIN*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-ACIN*BCIN':
        alumode = 3
    elif opcode == 'PCIN-ACIN*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(A+D)':
        alumode = 3
    elif opcode == 'PCIN-B*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN-B*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(D+A)':
        alumode = 3
    elif opcode == 'PCIN-B*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN-B*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(D-A)':
        alumode = 3
    elif opcode == 'PCIN-B*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN-B*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*A':
        alumode = 3
    elif opcode == 'PCIN-B*A-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*ACIN':
        alumode = 3
    elif opcode == 'PCIN-B*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-B*D':
        alumode = 3
    elif opcode == 'PCIN-B*D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(A+D)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D+A)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D-A)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN-BCIN*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*A':
        alumode = 3
    elif opcode == 'PCIN-BCIN*A-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*ACIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-BCIN*D':
        alumode = 3
    elif opcode == 'PCIN-BCIN*D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-C':
        alumode = 3
    elif opcode == 'PCIN-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-C-CONCAT':
        alumode = 3
    elif opcode == 'PCIN-C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-C-P':
        alumode = 3
    elif opcode == 'PCIN-C-P-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-CONCAT':
        alumode = 3
    elif opcode == 'PCIN-CONCAT-C':
        alumode = 3
    elif opcode == 'PCIN-CONCAT-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-D':
        alumode = 3
    elif opcode == 'PCIN-D*B':
        alumode = 3
    elif opcode == 'PCIN-D*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-D*BCIN':
        alumode = 3
    elif opcode == 'PCIN-D*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-P':
        alumode = 3
    elif opcode == 'PCIN-P-C':
        alumode = 3
    elif opcode == 'PCIN-P-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN-P-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)*B':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+A':
        alumode = 0
    elif opcode == 'PCIN>>17+A*B':
        alumode = 0
    elif opcode == 'PCIN>>17+A*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+A*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+A*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN*B':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(A+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D+A)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D-A)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+B*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*A':
        alumode = 0
    elif opcode == 'PCIN>>17+B*A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*ACIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+B*D':
        alumode = 0
    elif opcode == 'PCIN>>17+B*D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(A+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(A+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(ACIN+D)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(ACIN+D)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D+A)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D+A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D+ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D+ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D-A)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D-A)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D-ACIN)':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*(D-ACIN)+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*A':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*A+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*ACIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*ACIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*D':
        alumode = 0
    elif opcode == 'PCIN>>17+BCIN*D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+C':
        alumode = 0
    elif opcode == 'PCIN>>17+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+C+CONCAT':
        alumode = 0
    elif opcode == 'PCIN>>17+C+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+C+P':
        alumode = 0
    elif opcode == 'PCIN>>17+C+P+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+CONCAT':
        alumode = 0
    elif opcode == 'PCIN>>17+CONCAT+C':
        alumode = 0
    elif opcode == 'PCIN>>17+CONCAT+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+CONCAT+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+D':
        alumode = 0
    elif opcode == 'PCIN>>17+D*B':
        alumode = 0
    elif opcode == 'PCIN>>17+D*B+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+D*BCIN':
        alumode = 0
    elif opcode == 'PCIN>>17+D*BCIN+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+D+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+P':
        alumode = 0
    elif opcode == 'PCIN>>17+P+C':
        alumode = 0
    elif opcode == 'PCIN>>17+P+C+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17+P+CARRYIN':
        alumode = 0
    elif opcode == 'PCIN>>17-((A+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-((A+D)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((A+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((A+D)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((A+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A))':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A))':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN)*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN)*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN)*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN)*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-((D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(A+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D+A))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D-A))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*A)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*D)':
        alumode = 3
    elif opcode == 'PCIN>>17-(B*D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(A+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(A+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(ACIN+D))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D+A))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D+A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D+ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D-A))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D-A)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D-ACIN))':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*A)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*A+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*ACIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*D)':
        alumode = 3
    elif opcode == 'PCIN>>17-(BCIN*D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C+CONCAT)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C+CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C+P)':
        alumode = 3
    elif opcode == 'PCIN>>17-(C+P+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(CONCAT)':
        alumode = 3
    elif opcode == 'PCIN>>17-(CONCAT+C)':
        alumode = 3
    elif opcode == 'PCIN>>17-(CONCAT+C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(CONCAT+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D*B)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D*B+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D*BCIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D*BCIN+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)*B':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-(P)':
        alumode = 3
    elif opcode == 'PCIN>>17-(P+C)':
        alumode = 3
    elif opcode == 'PCIN>>17-(P+C+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-(P+CARRYIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-A':
        alumode = 3
    elif opcode == 'PCIN>>17-A*B':
        alumode = 3
    elif opcode == 'PCIN>>17-A*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-A*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-A*BCIN-CARRYIN':
        alumode = 3
        inmode_diff = -1
    elif opcode == 'PCIN>>17-A-CARRYIN':
        alumode = 3
        inmode_diff = -1
    elif opcode == 'PCIN>>17-ACIN':
        alumode = 3
    elif opcode == 'PCIN>>17-ACIN*B':
        alumode = 3
    elif opcode == 'PCIN>>17-ACIN*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-ACIN*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-ACIN*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(A+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D+A)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D-A)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-B*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*A':
        alumode = 3
    elif opcode == 'PCIN>>17-B*A-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*ACIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-B*D':
        alumode = 3
    elif opcode == 'PCIN>>17-B*D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(A+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(A+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(ACIN+D)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(ACIN+D)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D+A)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D+A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D+ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D+ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D-A)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D-A)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D-ACIN)':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*(D-ACIN)-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*A':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*A-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*ACIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*ACIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*D':
        alumode = 3
    elif opcode == 'PCIN>>17-BCIN*D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-C':
        alumode = 3
    elif opcode == 'PCIN>>17-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-C-CONCAT':
        alumode = 3
    elif opcode == 'PCIN>>17-C-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-C-P':
        alumode = 3
    elif opcode == 'PCIN>>17-C-P-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-CONCAT':
        alumode = 3
    elif opcode == 'PCIN>>17-CONCAT-C':
        alumode = 3
    elif opcode == 'PCIN>>17-CONCAT-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-CONCAT-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-D':
        alumode = 3
    elif opcode == 'PCIN>>17-D*B':
        alumode = 3
    elif opcode == 'PCIN>>17-D*B-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-D*BCIN':
        alumode = 3
    elif opcode == 'PCIN>>17-D*BCIN-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-D-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-P':
        alumode = 3
    elif opcode == 'PCIN>>17-P-C':
        alumode = 3
    elif opcode == 'PCIN>>17-P-C-CARRYIN':
        alumode = 3
    elif opcode == 'PCIN>>17-P-CARRYIN':
        alumode = 3
    elif opcode == 'RNDSIMPLE((A+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((A+D)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((A+D)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((A+D)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((A+D)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN)*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN)*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN)*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE((D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(A+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(A+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D+A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D-A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*(D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*A)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*A+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*ACIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*D)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(B*D+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(A+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(A+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(ACIN+D)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D+A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D+A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D+ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D-A))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D-A)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*(D-ACIN)+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*A)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*A+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*ACIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*ACIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*D)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(BCIN*D+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(CONCAT)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(CONCAT+CARRYCASCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D*B)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D*B+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D*BCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D*BCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(D+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+CARRYCASCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+CONCAT)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+P)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P+P+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17+CONCAT)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17+CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17+P)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(P>>17+P+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN+CONCAT)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN+CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN+P)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN+P+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17+CONCAT)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17+CONCAT+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17+P)':
        alumode = 0
    elif opcode == 'RNDSIMPLE(PCIN>>17+P+CARRYIN)':
        alumode = 0
    elif opcode == 'RNDSYM((A+D))':
        alumode = 0
    elif opcode == 'RNDSYM((A+D)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((A+D)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM((ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSYM((ACIN+D)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((ACIN+D)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM((D+A))':
        alumode = 0
    elif opcode == 'RNDSYM((D+A)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((D+A)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM((D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM((D+ACIN)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((D+ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM((D-A))':
        alumode = 0
    elif opcode == 'RNDSYM((D-A)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((D-A)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM((D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM((D-ACIN)*B)':
        alumode = 0
    elif opcode == 'RNDSYM((D-ACIN)*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM(A)':
        alumode = 0
    elif opcode == 'RNDSYM(A*B)':
        alumode = 0
    elif opcode == 'RNDSYM(A*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM(ACIN)':
        alumode = 0
    elif opcode == 'RNDSYM(ACIN*B)':
        alumode = 0
    elif opcode == 'RNDSYM(ACIN*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM(B*(A+D))':
        alumode = 0
    elif opcode == 'RNDSYM(B*(ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSYM(B*(D+A))':
        alumode = 0
    elif opcode == 'RNDSYM(B*(D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM(B*(D-A))':
        alumode = 0
    elif opcode == 'RNDSYM(B*(D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM(B*A)':
        alumode = 0
    elif opcode == 'RNDSYM(B*ACIN)':
        alumode = 0
    elif opcode == 'RNDSYM(B*D)':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(A+D))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(ACIN+D))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(D+A))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(D+ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(D-A))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*(D-ACIN))':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*A)':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*ACIN)':
        alumode = 0
    elif opcode == 'RNDSYM(BCIN*D)':
        alumode = 0
    elif opcode == 'RNDSYM(D)':
        alumode = 0
    elif opcode == 'RNDSYM(D*B)':
        alumode = 0
    elif opcode == 'RNDSYM(D*BCIN)':
        alumode = 0
    elif opcode == 'RNDSYM(P)':
        alumode = 0
    elif opcode == 'RNDSYM(PCIN)':
        alumode = 0

    return alumode, inmode_diff
