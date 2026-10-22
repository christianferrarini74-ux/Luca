# LUCA: visione del progetto

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

## Scopo

LUCA è un esperimento su una forma diversa di intelligenza artificiale: un'architettura cognitiva persistente che apprende modificando la propria memoria esplicita, invece di modificare principalmente un insieme grande e opaco di pesi.

Non vuole competere con gli LLM frontier nella generazione ampia o nella conoscenza pre-addestrata. Vuole dimostrare che un sistema può ricevere una base limitata, essere istruito con linguaggio semplice, conservare ciò che apprende, correggerlo e usarlo in seguito attraverso una struttura di memoria tracciabile.

L'espansione di lavoro del nome è **Logical, Updatable, Cell-based, Addressable intelligence**. È una descrizione di lavoro, non una proprietà già dimostrata.

## Tesi centrale

In un LLM con retrieval augmentation, l'informazione esterna viene recuperata e fornita al modello come contesto. La struttura sottostante del modello non cambia necessariamente.

In LUCA, l'informazione importante diventa parte del sistema:

```text
istruzione semplice
    → celle, assertion e percorsi indirizzati
    → cambiamento della memoria interna persistente
    → pensieri futuri avviati dalla struttura cambiata
```

Le celle contengono contenuto, stato, evidenze e storia. Gli archi sono indirizzi diretti senza semantica. Il grafo non è un allegato al sistema cognitivo: è la sua memoria nativa.

## La memoria è il modello

LUCA è progettato dalla gerarchia di storage verso l'alto:

```text
SSD   cervello completo e persistente
RAM   contesto attivo e vicinato topologico
VRAM  working set ristretto per un pensiero
```

Il cervello non deve stare tutto in RAM o VRAM. Un pensiero attraversa una regione delimitata di una memoria persistente più grande. La GPU accelera working set selezionati ma non possiede il cervello.

## Ruolo di LLM, RAG e strumenti esterni

LUCA può usare modelli linguistici, retrieval, biblioteche, ricerca, calcolatori, sensori o altri moduli come supporto. Non sostituiscono la memoria di Luca:

```text
informazione esterna o istruzione utente
    → lezione / evidenza proposta
    → validazione e provenienza
    → memoria interna di LUCA
```

Un risultato di retrieval resta evidenza esterna finché non attraversa questo percorso.

## Cosa deve provare il primo dimostratore

Il primo dimostratore è volutamente piccolo. Deve tenere una conversazione leggera in un dominio delimitato e dimostrare che una persona può insegnare un fatto, che Luca lo converte in celle ispezionabili, lo recupera dopo il riavvio, mantiene un breve contesto, dichiara ciò che non sa, riceve correzioni senza cancellare silenziosamente la storia e conserva tracce e provenienza.

Questo è il proof of concept. Sarà valutato su micro-mondi controllati, anche inventati, per evitare che la conoscenza pre-addestrata di un LLM venga scambiata per apprendimento di Luca.

## Cosa non significa successo

Il successo non significa eguagliare fluidità, conoscenza enciclopedica o ragionamento generale di un LLM. Significa dimostrare una forma diversa e utile di crescita:

```text
conoscenza iniziale limitata
+ istruzione incrementale
+ persistenza immediata
+ correzione e provenienza
+ recupero tracciabile e ragionamento locale
= memoria cognitiva in crescita
```

## Disciplina scientifica

Ogni tesi deve essere verificabile. Conserviamo versioni del curriculum, fonti, input, risultati attesi, tracce, budget, benchmark, fallimenti e revisioni. Quando un'ipotesi fallisce, cambiamo il design invece di nascondere il risultato dietro un modello opaco più grande.
