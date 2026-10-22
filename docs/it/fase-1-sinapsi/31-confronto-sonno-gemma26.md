# Confronto del raggruppamento nel sonno con Gemma 26B A4B

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../sleep-gemma26-comparison.md).

Implementazione successiva: [classificazione separata dal calcolo degli archi](32-classificazione-e-pianificazione-archi.md).
Le osservazioni sotto conservano la precedente interfaccia di proposta numerica.

## Protocollo controllato

Ripetere la [prova dell'arresto all'obiettivo](30-arresto-riorganizzazione-obiettivo.md)
con il modello installato esatto `google/gemma-4-26b-a4b`, Gemma 4 26B A4B Q8_0
(26B-A4B nel catalogo locale). Confronto con `google/gemma-4-e2b` Q4_K_M,
dimensione di catalogo 4,6B. I nomi non indicano due modelli densi differenti
solo per numero di parametri: cambiano anche architettura/parametri attivi,
tokenizer e quantizzazione. È un confronto locale fra modelli, non una prova
causale isolata sul numero dei parametri.

Quattro DB temporanei nuovi, stesso grafo di 153 nodi, 52 archi esterni,
soglie 50/45, famiglia canonica, controlli, Bibbia originale, worker periodico
reale e inattività/controllo diagnostici a un secondo. Nessuna cronologia,
correzione semantica o secondo revisore. Restano budget contesto 70.000 token,
temperatura 0, output manutenzione 8.192 token e timeout provider 180 secondi.

```powershell
python -m luca_memory.sleep_check --model google/gemma-4-26b-a4b --repeat 4
```

Riferimento: `D:/Test/Luca/sleep-check-20261022-152757-065979.json`.
Esaminare tutti i gruppi grezzi proposti, compresi quelli scartati dal Core.
Controllare appartenenza tematica, compatibilità del titolo e limite richiesto
di otto membri, separatamente da selezione all'obiettivo, integrità strutturale,
riapertura e ripristino. Il campo strutturale `passed` non è accettazione semantica.

Il modello maggiore è caricato solo per questa prova: contesto richiesto 70.000,
effettivo backend 70.144, un solo slot parallelo. E2B preesistente rimane caricato
con le proprie impostazioni. Nessuna modifica a config, Bibbia, codice runtime,
dipendenze o memoria personale.

## Riferimento del modello piccolo

Con lo stesso codice, entrambe le prove E2B avevano proposte sufficienti a
raggiungere l'obiettivo, ma entrambe violavano il limite richiesto di otto
membri. Il Core selezionava un gruppo omogeneo per prova, ottenendo 44/40 archi.
Nella prima un gruppo uscente scartato mescolava Botanica e Astronomia sotto
“Astronomia”; nella seconda tutti e quattro i gruppi grezzi erano omogenei.
La sola purezza del piano applicato avrebbe nascosto un errore reale della
proposta. Durate worker di riferimento: 15,005 e 16,612 secondi. Sono osservazioni
locali, non un benchmark standardizzato di velocità.

## Risultato delle quattro prove

Rapporto: `D:/Test/Luca/sleep-check-20261022-153755-744261.json`.
Tutti e quattro gli input rubrica/vincoli coincidono con il riferimento E2B;
identici anche hash delle istruzioni di sistema complete e impostazioni della
manutenzione. Cronologia vuota, input di 2.643 token del modello, nessun estratto
segnalato. Non emerge un problema di vicini nascosti o capacità del contesto.

| Prova | Proposta grezza | Riduzione totale | Esito | Durata worker |
| --- | --- | ---: | --- | ---: |
| 1 | Tre gruppi da quattro: Botanica entrante, Astronomia entrante, Botanica uscente | 9 | Applicata, 52→43; riapertura e ripristino esatto superati | 133,532 s |
| 2 | Due gruppi da quattro: Botanica entrante e uscente | 6 | Rifiutata prima dell'applicazione: porterebbe a 46, non <=45 | 125,832 s |
| 3 | Gli stessi due gruppi da quattro | 6 | Rifiutata prima dell'applicazione | 124,242 s |
| 4 | Gli stessi due gruppi da quattro | 6 | Rifiutata prima dell'applicazione | 128,556 s |

Tutti i **nove gruppi grezzi**, incluse le proposte rifiutate, hanno membri
tematicamente omogenei e titoli Botanica/Astronomia compatibili. Sono da quattro
membri, rispettando il massimo richiesto di otto. Nessun mescolamento tematico
osservato in queste quattro prove. È distinto dal successo della manutenzione
completa, ottenuto solo nella prima. Il risultato 43 è quello più vicino con
gruppi interi: due riducono sei archi, tre ne riducono nove; manca una combinazione
con riduzione esatta di sette.

Nelle prove 2–4 la proposta offre una riduzione complessiva insufficiente.
Il Core restituisce `The proposed grouping does not reach edge_target.`:
rifiuta il piano prima della transazione applicativa, anziché applicarlo
parzialmente o fingere che 46 soddisfi l'obiettivo. Queste prove rifiutate non
hanno verifiche di riapertura/ripristino riuscite e non sono manutenzioni
superate. Il diagnostico termina correttamente con codice 1, pur con temi separati.

Non viene acquisito il ragionamento privato e non è dimostrato *perché* il modello
si fermi: osserviamo una proposta insufficiente, non una causa aritmetica interna
accertata. Dire «otto archi rimossi» per due gruppi da quattro sarebbe errato:
otto archi originari diventano due connettori, riduzione netta sei.

## Interpretazione e confine della chiusura

In questo grafo facile ed etichettato il modello maggiore elimina il sintomo
del mescolamento osservato prima e rispetta la dimensione richiesta. Il risultato
sostiene un problema semantico dipendente dal proponente, non una trasformazione
del grafo osservata come corruttrice. Non dimostra che la differenza dipenda solo
dal numero dei parametri o che questo modello non possa mai mescolare temi.

**Il funzionamento autonomo completo del sonno non è chiuso cambiando modello.**
Tre proposte su quattro non rispettano ancora il contratto numerico esistente.
Un intervento futuro potrebbe restituire al proponente gli errori di validazione
per una correzione limitata prima dell'applicazione, senza indebolire le soglie
o cambiare i membri dei gruppi nel Core. È un possibile passo successivo, non
implementato né dimostrato funzionante in questo confronto. Bibbia non ottimizzata.

L'unica operazione applicata conserva integrità, rubriche familiari e
raggiungibilità e supera riapertura/ripristino. Non emerge quindi una nuova
violazione delle proprietà di trasformazione della memoria, ma resta un limite
nel completamento della proposta. Sono evidenze controllate, non una
certificazione su biblioteche estese.

## Pulizia e verifiche

Scaricato solo il 26B caricato per l'esperimento, dopo che era tornato inattivo.
E2B resta caricato con contesto originale 131.072 e quattro slot paralleli.
Memoria GPU tornata ai valori iniziali 6.935/14/14 MiB, utilizzo zero. Tutti
i quattro worker diagnostici terminati con join; DB temporanei rimossi, rapporti
conservati.

Suite portabile: 280 test Python, OK con sette verifiche opzionali hardware/servizi
saltate; Ruff pulito. Questa consegna aggiunge solo documentazione: codice di
produzione, configurazione, Bibbia, dipendenze e memoria personale invariati.
