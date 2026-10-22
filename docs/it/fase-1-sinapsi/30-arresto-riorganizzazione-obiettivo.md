# Riorganizzare solo fino all'obiettivo configurato

2026-10-22. [English](../../maintenance-target-stop.md).

## Comportamento corretto

La politica 50/45 ha due soglie: avvio automatico solo oltre 50 archi esterni,
arresto a 45 o al valore raggiungibile più vicino sotto 45 se l'ultimo gruppo
intero non è divisibile. Non significa «applicare tutti i gruppi validi purché
il risultato sia <=45». La [precedente verifica del sonno](29-verifica-riorganizzazione-sonno.md)
ha mostrato questa riorganizzazione eccessiva, distinta dal problema semantico.

Il Core ora convalida tutti i gruppi prima di modificare e seleziona un
sottoinsieme di gruppi interi che minimizza l'eccesso di riduzione rispetto a
`grado_iniziale-edge_target`. A parità sceglie meno gruppi, poi l'ordine originale.
Non rimuove o redistribuisce arbitrariamente membri di un gruppo proposto dal
modello. I gruppi non selezionati non vengono creati e i loro archi restano
diretti. Se le proposte valide complessive non raggiungono l'obiettivo, nessuna
scrittura. Al limite obiettivo o sotto, resta un no-op. Anche il manuale usa
questa regola; l'automatico resta riservato a gradi strettamente oltre
`edge_upper`. Tutte le soglie derivano dalla configurazione.

Il selettore mantiene stati delle riduzioni inferiori al fabbisogno; raggiungere
la soglia è terminale, quindi non aggiunge gruppi dopo l'obiettivo. È una scelta
strutturale, non un raggruppamento semantico o una distillazione. L'anteprima
mostra il piano selezionato, l'applicazione lo riconvalida e il registro atomico
di ripristino contiene solo i gruppi applicati. I ripristini già confermati
restano utilizzabili.

## Esempi e accettazione

- Grado 52, obiettivo 45: preferire un gruppo proposto di otto membri
  (riduzione sette) a uno precedente di tredici (riduzione dodici): arresto a 45.
- Grado 52, solo quattro gruppi da tredici: applicarne **uno**, ottenendo 40,
  non tutti e quattro ottenendo 4. La proposta non offre riduzioni inferiori.
- Riduzioni 6, 4, 3 e fabbisogno 7: scegliere 4+3 anziché il greedy 6+3.
- I controlli già a 50/45 non diventano candidati automatici.

L'adapter richiede inoltre `max_members=min(edge_upper-1, max(2,fabbisogno+1))`:
otto nel caso 52→45. La richiesta da sola non garantisce il rispetto da parte
del modello. La convalida strutturale Core mantiene fino a `edge_upper-1`
membri; il ripiego sul gruppo intero più vicino gestisce proposte più grandi
senza inventare sottogruppi semantici. La modifica impedisce gli accorpamenti
superflui, ma non garantisce esattamente 45 per ogni risposta dell'LLM.

## Ripetizione con Gemma reale

Stesso modello, Bibbia originale, grafo sintetico originale di 153 nodi e vero
worker in inattività; solo DB temporanei. Rapporto:
`D:/Test/Luca/sleep-check-20261022-152757-065979.json`.

| Prova | Proposta del modello | Piano applicato | Durata worker |
| --- | --- | --- | ---: |
| 1 | Due gruppi, riduzioni 8 e 11 | Un gruppo entrante Botanica da nove membri: **52→44** | 15,005 s |
| 2 | Quattro gruppi, riduzione 12 ciascuno | Un gruppo entrante Botanica da tredici membri: **52→40** | 16,612 s |

Superati tutti i controlli strutturali, rubriche familiari, raggiungibilità,
riapertura e ripristino esatto. Entrambi i gruppi selezionati hanno membri
tematicamente omogenei nel caso controllato. Non è una prova dell'accuratezza
dei titoli o dell'affidabilità generale; i gruppi scartati non sono certificati.
Nella prima prova un gruppo uscente scartato, chiamato “Astronomia”, mescolava
argomenti. Le proposte grezze rimangono nel rapporto: la selezione non deve
nascondere questa evidenza.

Gemma ha ignorato in entrambe le prove il limite richiesto di otto membri.
I piani scendono quindi di uno/cinque archi sotto l'obiettivo, non esattamente
a 45. Imporre proposte LLM più piccole o verificare indipendentemente la semantica
sarebbe un lavoro distinto. Bibbia, config, dipendenze e memoria personale invariati.

## Verifiche

Nuovi test: preferenza dell'obiettivo esatto su grafo reale, minimo scarto con
gruppi indivisibili, spareggi, proposte insufficienti, fabbisogno comunicato
dall'adapter e 100 confronti riproducibili con enumerazione esaustiva dei
sottoinsiemi. Restano attivi integrità, crash di processo, navigazione familiare
e ripristino.

Consegna: 280 test Python, OK (sette verifiche opzionali hardware/servizi saltate),
19 JavaScript superati, Ruff e `git diff --check` puliti. Anche un piano costruito
manualmente con gruppi superflui viene rifiutato all'applicazione senza scritture.
