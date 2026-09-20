print()
print("SchnulpFolgen 4.4G by gismo.pracht@proton.me")
print("Es ist Teamwork - Besuchen Sie den Matheplaneten")
print()

import math
import time
from datetime import timedelta
import random
import os
import sympy

##################################################################
# Defaultwerte, koennen in dieser reihenfolge durch aufrufparameter
# ueberschrieben werden
addsign  = "7" # Diese Zahl wird bearbeitet
base=1; # startzahl mit der begonnen wird
logtoken = "allthelog.log"
###############################################################
# Konfiguration des Programmes
prae=True # True=voranstellen False=hintenanhaengen
report = 100000 # Ausgabe der erreichten startzahl in Intervallen
cnt4deb = 1000 # Ausgabe Index innerhalb der Folge
pftimeout = 1800 # Timeout fuer Primfaktorzerlegung
purge = 200 # in vielfachen von report
purgelen = 20000000 # clear attractors on len of set
###############################################################

import sys
if len(sys.argv) > 1: addsign=sys.argv[1]; print(f"Erweiterungszeichen ist {addsign}")
if len(sys.argv) > 2: base=int(sys.argv[2]); print(f"Erster Folgestartwert {base}")
if len(sys.argv) > 3: logtoken=sys.argv[3]+".log"; print("Logged by Token",logtoken)
base_formatiert="N="+addsign+" start="+str(base);basestart=base
print("Timeout Faktorisierung",pftimeout,"seconds")

if prae: praesign="_vorab_"
else: praesign="_nachgestellt_"

from sympy import isprime, pollard_rho, primerange
import signal

def glog(myline):
    with open(logtoken,'a') as logfile:
        logfile.write(myline+"\n")
        logfile.close()

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
        glog(base_formatiert+" Timeout("+str(pftimeout)+"s) "+str(number))
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
purgecnt=0

# genauer macht das redo wenn ein neuer attraktor gefunden wurde
################################################################

def genauer(number):
    
    factorcache.clear()
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
            factorcache[now]=div
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
        print(base_formatiert,"cnt="+str(cnt),laufzeit+"s Schleife erreicht bei",now_formatiert)
        print(base_formatiert,"Neue Schleife Eintrittspunkt",minimum,"Länge der Schleife",seqcnt)
        laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
        print("Bekannte Schleifen: ",loopstartbymin,)
        print()
        
# Nun die Schleifen der Reihe nach berechnen
######################################################

if prae: signstr="mit vorangestellter "+addsign
else: signstr="mit nachgestellter "+addsign

print("Folgenberechnung ab",base_formatiert,signstr)
print()

loopstart=set(); attractors=set();
maximum=0

while True:

    nowdone=set(); now=base; 
    fertig=False; newloop=False; cnt=0
    
    while not fertig:

        # Hatten wir diesen Wert schon ?
        if now in nowdone:
            # Die Schleife geschlossen (eine neue ist es)
            fertig=True; newloop=True; loopstart.add(now);
            print(base_formatiert,"Attraktor",now)     
        elif now<base or now in attractors:
            # Attraktor fuer alte Schleife erreicht
            fertig=True;
        else:
            # es geht einfach weiter.
            nowdone.add(now)
            attractors.add(now)
          
        # Also weiter der Folge folgen
        div=kleinster_teiler(now)
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
            attractors = {x for x in attractors if x > base}
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            print(base_formatiert,laufzeit,"loops =",loopstartbymin)
            purgecnt+=1
            if purgecnt>=purge or len(attractors)>purgelen:
                if purgecnt>=purge : print("Attractors len =",round(len(attractors)/1000000,2)," Mio periodically purged.")
                else: print("Attractors len =",round(len(attractors)/1000000,2)," Mio purged (length).")
                purgecnt=0
                attractors.clear()
                for myloop in loopstartbymin:
                    attractors.add(myloop)
        
    # und weiter geht es mit dem nächsten Startwert oben in die Loop.
    base+=1;
    base_formatiert = "N="+addsign+" start="+f"{base:_}".replace("_", ".")

# Dies wird nie erreicht.
print("Habe fertig")
