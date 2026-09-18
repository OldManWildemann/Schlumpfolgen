print()
print("SchnulpFolgen 4.2 by gismo.pracht@proton.me")
print("Es ist Teamwork - Besuchen Sie den Matheplaneten")
print()

import math
import time
from datetime import timedelta
import random
import os
import sympy

addsign  = "7" # Diese Zahl wird bearbeitet
prae=True # True=voranstellen False=hintenanhaengen

###############################################################
# Konfiguration des Programmes
base=1; # startzahl mit der begonnen wird
report   = 100000 # Ausgabe der erreichten startzahl in Intervallen
maxprime = 200000000 # max Primzahl die vorberechnet wird
sec4pollard = 60 # sec maximal pro faktorisierung
cnt4deb = 1000 # Ausgabe Index in Folge
pftimeout = 120
alldonemax = 10000000 # nur bis hierhin wird alldone erfasst
         # alldone muss groesser sein als die groesste bisher
         # bekannte basis einer schleife, sonst wird diese
         # unter Umstaenden erneut gefunden mit anderem 
         # einsprungspunkt...
###############################################################

import sys
if len(sys.argv) > 1: addsign=sys.argv[1]; print(f"Erweiterungszeichen ist {addsign}")
if len(sys.argv) > 2: base=int(sys.argv[2]); print(f"Erster Folgestartwert {base}")

base_formatiert="N="+addsign+" start="+str(base);basestart=base

if prae: praesign="_vorab_"
else: praesign="_nachgestellt_"

from sympy import isprime, pollard_rho, primerange
import signal

# primefactors mit Timeout ueber signal
#######################################

# 1. Definiere die Ausnahme für das Timeout
class TimeoutException(Exception):
    pass

# 2. Signal-Handler-Funktion, die beim Timeout aufgerufen wird
def timeout_handler(signum, frame):
    raise TimeoutException("Faktorisierung nach "+str(pftimeout)+"s nicht abgeschlossen.")

def my_primefactors(number):
    # Registriere den Signal-Handler für das Alarmsignal (SIGALRM)
    signal.signal(signal.SIGALRM, timeout_handler)
    # Starte den Timer (Countdown in Sekunden)
    signal.alarm(pftimeout)
    
    try:
        result = sympy.primefactors(number)[0]
        return result
    except TimeoutException as e:
        print("[Timeout]",base_formatiert,"number",number)
        return 0
    finally:
        signal.alarm(0)
    
# Kleinster Teiler fasst alles zur faktorisierung zusammen
##########################################################

def kleinster_teiler(n):
    if isprime(n) or n==1: return 1   
    for kleine_prim in primerange(2, 10000):
        if n % kleine_prim == 0:
            return kleine_prim
    return my_primefactors(n)

loopstartbymin=[]
factorcache={}
start_time=time.time()

# genauer macht das redo wenn ein neuer attraktor gefunden wurde
################################################################

def genauer(number):

    thisdone=[]; now=number; cnt=0
    newloop=False; known=False; overflow=False; maximal=0

    base_formatiert = "N="+addsign+" redo start="+f"{base:_}".replace("_", ".")

    while not (known or newloop):

        # Hatten wir diesen Wert schon ?
        cnt+=1
        if now in thisdone: newloop=True;
        thisdone.append(now);

        div=kleinster_teiler(now)
        if div>0:
            if prae: now = int(addsign+str(now//div))
            else: now = int(str(now//div)+addsign)
        else: overflow=True
        # Ende der Loop für einen bestimmten Startwert
 
    if newloop:
        # Aufbereiten gefundener Schleife
        begin=False
        minimum=maximum
        sequencestr=""
        seqcnt=0
        seqpos=0
        for myloop in thisdone:
            if myloop==now: begin=True
            if begin:
                seqcnt+=1
                if myloop<minimum:
                    minimum=myloop
                    seqpos=len(sequencestr)
                if myloop in factorcache and factorcache[myloop]!=1:
                        sequencestr+=str(myloop)+"("+str(factorcache[myloop])+"), "
                else: sequencestr+=str(myloop)+"(prime), "
                
        # umordnen sodass minimum vorne + in Datei schreiben
        sequencestr=sequencestr[seqpos:]+\
            sequencestr[:seqpos]+str(minimum)
        outfile=open(addsign+praesign+str(minimum)+".loop","w")
        outfile.write(sequencestr)
        outfile.close()
        
        # und diese vermerken und ausgeben
        loopstartbymin.append(minimum)
        loopstartbymin.sort()
        laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
        now_formatiert = f"{now:_}".replace("_", ".")
        
        print()
        print(base_formatiert,"cnt="+str(cnt),laufzeit+"s Loop erreicht bei",now_formatiert)
        print("Neue Schleife #"+str(len(loopstart)),"@",minimum,
              "Länge der Sequenz:",seqcnt)
        laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
        print("Bekannte Schleifen: ",loopstartbymin,)
        print()
        
# Nun die Schleifen der Reihe nach berechnen
######################################################

if prae: signstr="mit vorangestellter "+addsign
else: signstr="mit nachgestellter "+addsign

print("Folgenberechnung ab",base_formatiert,signstr)
print()

loopstart=set(); alldone=set();
maximum=0

while True:

    nowdone=set(); now=base; 
    fertig=False; newloop=False; cnt=0
    
    while not fertig:

        # Hatten wir diesen Wert schon ?
        if now in nowdone:
            fertig=True; newloop=True; loopstart.add(now);
            print("Neue Schleife",loopstart)     
        elif now in alldone:
            fertig=True;
        else:
            nowdone.add(now)
            if now<alldonemax: alldone.add(now)
          
        # Also weiter der Folge folgen
        div=kleinster_teiler(now)
        factorcache[now]=div
        if div>0:
            if prae: now = int(addsign+str(now//div))
            else: now = int(str(now//div)+addsign)
        else: fertig=True

        cnt+=1
        if len(loopstartbymin)>0: loopstartstr=str(loopstartbymin)
        else: loopstartstr="schleifen=None"
        if cnt%cnt4deb==0: 
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            print(base_formatiert,"cnt="+str(cnt),laufzeit+"s",loopstartstr)
        if now>maximum:
            now_formatiert = f"{now:_}".replace("_", ".")
            maximum=now; print(base_formatiert,"cnt="+str(cnt),now_formatiert)
        # Ende der Loop für einen bestimmten Startwert
     
    if newloop: genauer(now)  
    if base%report==0: 
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            print(base_formatiert,laufzeit,"loops =",loopstartbymin)
        
    # und weiter geht es mit dem nächsten Startwert oben in die Loop.
    base+=1;
    base_formatiert = "N="+addsign+" start="+f"{base:_}".replace("_", ".")

# Dies wird nie erreicht.
print("Habe fertig")
