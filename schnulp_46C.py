print()
print("Version 4.6C for linux, sympy, msieve, factordb.com")
print("Questions? Visit matheplanet.de - contact user gonz")
print("Public Domian under CC0 1.0 (Creative Commons Zero)")
print()

import math
import time
from datetime import timedelta
import random
import os
import sympy
import subprocess
import re
import sys
from sympy import isprime, pollard_rho, primerange
import signal
import json
import urllib.parse
import urllib.request

##################################################################
# Defaultwerte, koennen in dieser reihenfolge durch aufrufparameter
# ueberschrieben werden
addsign  = "7" # Diese Zahl wird bearbeitet
base=1; # startzahl mit der begonnen wird
###############################################################
# Konfiguration des Programmes
msieve_path = "msieve"
report = 100000 # Ausgabe der erreichten startzahl in Intervallen
cnt4deb = 1000 # Ausgabe Index innerhalb der Folge
pftimeout = 60 # Timeout fuer Primfaktorzerlegung mit sympy
purge = 200 # in vielfachen von report, forced
purgelen = 20000000 # clear attractors on len of set
###############################################################

if len(sys.argv) > 1: addsign=sys.argv[1]; print(f"Erweiterungszeichen ist {addsign}")
if len(sys.argv) > 2: base=int(sys.argv[2]); print(f"Erster Folgestartwert {base}")
base_formatiert="N="+addsign+" start="+str(base);basestart=base
print("Timeout Faktorisierung sympy",pftimeout,"seconds")


def check_factordb(number):
        
    url = f"https://factordb.com/api?query={urllib.parse.quote(str(number))}"
    try:
        # Anfrage senden mit einem Standard-User-Agent
        req = urllib.request.Request(url,
                    headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Status-Code-Bedeutungen übersetzen
            status_labels = {
                "C": "Composite (Zusammengesetzt, keine Faktoren bekannt)",
                "CF": "Composite, Factor known (nicht alle Faktoren bekannt)",
                "FF": "Fully Factored (Komplett zerlegt)",
                "P": "Prime (Primzahl)",
                "PR": "Probable Prime (Wahrscheinliche Primzahl)",
                "U": "Unknown (Unbekannt)",
                "Unit": "Unit (Eins / Neutrales Element)",
                "N": "No status (Kein Status)"
            }
            
            status = data.get("status", "U")
            status_text = status_labels.get(status, f"Unbekannter Status ({status})")
            
            print(f"Req factorDB {number}")
            if status=="FF":
                factors=[]
                for factor_info in data.get("factors", []):
                    factor = int(factor_info[0]) # Der Primfaktor als Zahl
                    # print("Faktor:",factor)
                    factors.append(factor)
                if len(factors)>0:
                    print("factorDB",number,":",factors[0])
                    return factors[0] # we got a factor
                else: return 0
            elif status=="P": return 1 # is prime
            else: return 0
            
    except Exception as e:
        print("number =",number)
        print(f"Fehler bei der Abfrage: {e}")
      
    return 0 # Timeout unseres Verfahrens nicht durch factordb behebbar


def factor_with_msieve(number):
    command = [msieve_path, "-v", str(number)]
    mystarttime = time.time()
    factors = []
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Leitet auch eventuelle Fehler in den Standardkanal
        text=True,                 # Sorgt dafür, dass wir Text (Strings) statt Bytes erhalten
        bufsize=1                  # Zeilenbasiertes Buffering für Echtzeit-Ausgabe
    )
    
    for line in process.stdout:
        if "factor:" in line:
            match = re.search(r'factor:\s+(\d+)', line)
            if match:
                factor = match.group(1)
                if factor not in factors:
                    factors.append(factor)
                    
    # Wartet, bis der Prozess vollständig beendet ist
    process.wait()
    print("msieve done",str(round(time.time()-mystarttime,2))+"s",factors)
    
    return factors
    

# sympy.primefactors mit Timeout ueber signal
###################################################

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Faktorisierung nach "+str(pftimeout)+"s nicht abgeschlossen.")

def my_primefactors(number):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(pftimeout)
    
    try:
        result = sympy.primefactors(number)[0]
        return result
    except TimeoutException as e:
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
    div=my_primefactors(n)
    if div>0:
        return div
    else:
        print("msieve",n,"("+str(len(str(n)))+")")
        gefundene_faktoren = factor_with_msieve(n)
        if len(gefundene_faktoren)>0:
            return int(gefundene_faktoren[0])
        else:
            first=True
            while div==0:
                if first:
                    first=False
                    waitTime=60
                else:
                    waitStart=time.time()
                    while time.time()<waitStart+waitTime: pass
                    if waitTime<1800:
                        waitTime=waitTime*2 
                    else: waitTime:3600     
                # dann factordb befragen.
                div=check_factordb(now)
    return div

#########################################################################
    

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
            now = int(addsign+str(now//div))
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
        outfile=open(addsign+"_"+str(minimum)+".loop","w")
        outfile.write(sequencestr)
        outfile.close()
        
        # und diese vermerken und ausgeben
        loopstartbymin.append(minimum)
        loopstartbymin.sort()
        loopstartstr=str(loopstartbymin)
        loopstartstr=loopstartstr.replace(" ","")
        laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
        now_formatiert = f"{now:_}".replace("_", ".")    
        # print(base_formatiert,"cnt="+str(cnt),laufzeit,"Schleife erreicht bei",now_formatiert)
        print(base_formatiert+"|"+laufzeit,"minimum="+str(minimum),"len="+str(seqcnt),"loops="+loopstartstr)

        
        
# Nun die Schleifen der Reihe nach berechnen
######################################################

signstr="mit vorangestellter "+addsign

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
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            laufzeit = laufzeit.replace(" day,","d")
            print(base_formatiert+"|"+laufzeit,"Attraktor",now)     
        elif now<base or now in attractors:
            # Attraktor fuer alte Schleife erreicht
            fertig=True;
        else:
            # es geht einfach weiter.
            nowdone.add(now)
            attractors.add(now)
          
        # Also weiter der Folge folgen
        div=kleinster_teiler(now)
        if div>0: now = int(addsign+str(now//div))
        else: fertig=True

        cnt+=1
        if len(loopstartbymin)>0: 
            loopstartstr=str(loopstartbymin)
            loopstartstr=loopstartstr.replace(" ","")
        else: loopstartstr="None"
        if cnt%cnt4deb==0: 
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            print(base_formatiert+"|"+laufzeit,"cnt="+str(cnt),"loops="+loopstartstr)
        if now>maximum:
            now_formatiert = f"{now:_}".replace("_", ".")
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            laufzeit = laufzeit.replace(" day,","d")
            maximum=now; print(base_formatiert+"|"+laufzeit,"cnt="+str(cnt),"max="+now_formatiert)
        # Ende der Loop für einen bestimmten Startwert
     
    if newloop: genauer(now)  
    if base%report==0: 
            attractors = {x for x in attractors if x > base}
            laufzeit = str(timedelta(seconds=int(time.time()-start_time)))
            laufzeit = laufzeit.replace(" day,","d")
            print(base_formatiert+"|"+laufzeit,"loops="+loopstartstr)
            purgecnt+=1
            if purgecnt>=purge or len(attractors)>purgelen:
                if purgecnt>=purge : print("Attractors len="+str(round(len(attractors)/1000000,2))+"M periodically purged.")
                else: print("Attractors len="+str(round(len(attractors)/1000000,2))+"M purged by length.")
                purgecnt=0
                attractors.clear()
                for myloop in loopstartbymin:
                    attractors.add(myloop)
        
    # und weiter geht es mit dem nächsten Startwert oben in die Loop.
    base+=1;
    base_formatiert = "N="+addsign+" start="+f"{base:_}".replace("_", ".")

# Dies wird nie erreicht.
print("Habe fertig")
