# Revisione di coerenza della documentazione

2026-10-22. [English](../../documentation-audit.md).

## Perché serviva la revisione

I README precedenti accumulavano aggiornamenti cronologici sopra le istruzioni
della demo iniziale. Descrivevano insieme il runtime LLM/CUDA attuale e assenza
di LLM/dipendenze, un modello superato e l'apprendimento iniziale di asserzioni.
Le guide storiche parlavano ancora di processo Vite, porte/chiavi frontend e
risposte chat “verificate”. L'indice italiano presentava inoltre vecchi piani e
integrazione Cesare come obiettivi attivi: non rappresentano il prodotto corrente.

## Riferimento attuale

Luca è memoria sinaptica esterna, non un LLM concorrente. Il Core proprietario
gestisce nodi/archi/famiglie, indici, residenza, modifiche atomiche e
riorganizzazione. I produttori creano/suddividono i contenuti; chat e cruscotto
sono consumer di prova. Produzione dei contenuti, PDF, distillazione, costruzione
di biblioteche e integrazione Cesare sono fuori ambito.

Avvio/configurazione confrontati con `config.yaml`, `config.py`, `run_luca.py`,
`api.py`, `adapters.py` e connettore: unico server/avvio Python, frontend statico
incluso, dipendenza PyYAML, profilo Gemma E2B, 70.000 token, scelta CUDA/host
esplicita e storage esterno. Conteggio nativo dei token, navigazione/classificazione
strutturate e calcolo Core distinti dalla qualità del ragionamento del modello.
Le possibilità del connector non certificano ogni provider per l'adapter
applicativo. Nessuna promessa di risposta “verificata” o fallback automatico alle regole.

## Metodo di controllo dell'intera documentazione

Inventario iniziale: 94 file Markdown versionati, di cui 84 sotto `docs/`.
La revisione cataloga i ruoli, controlla i link locali in tutti i documenti,
confronta le indicazioni operative attuali con codice/config e distingue
specifiche/risultati storici dalle guide vigenti. Non riconvalida retroattivamente
ogni vecchio esperimento né dichiara nuove esecuzioni hardware passate.

- Riscritti entrambi i README: ambito, architettura, prerequisiti, avvio, verifiche
  e limiti effettivi.
- Aggiornate configurazione, cruscotto e connettore in entrambe le lingue.
- Nuovi indici completi italiano/inglese: **96 documenti**, distinti in
  **15 guide/riferimenti attuali, 79 documenti/copie storici, due fixture**.
- Avviso storico esplicito aggiunto a 70 originali, conservando corpo ed evidenze
  della fase senza riscriverli per farli apparire attuali.
- Conservate nove versioni precedenti: due README, indice italiano e sei guide
  operative. Collegamenti relativi adattati quando necessario per il nuovo percorso.
- Guide operative correnti bilingui. Sei primi originali di fase rimangono
  documenti storici soltanto italiani: limite dichiarato nel catalogo.
- Manuali fittizi, Bibbia runtime e dati di prompt sperimentali/legacy non
  modificati né promossi silenziosamente a contratto vigente.

È una revisione di ambito/stato e coerenza operativa, non una dichiarazione che
tutte le architetture storiche siano implementate o le ipotesi dimostrate.
I test documentali non visitano link web esterni. I rapporti locali sotto
`D:/Test/Luca` sono artefatti di questa macchina, non input versionati; il
repository conserva fixture e comandi per ripetere gli esperimenti.

## Regressioni e consegna

Cinque test documentali verificano destinazioni Markdown locali fuori dagli
esempi in blocchi di codice, copertura dei cataloghi nelle due lingue,
modello/database rispetto allo YAML, stato storico esplicito e assenza delle
vecchie affermazioni demo nei README correnti. Test portabili, senza GitHub,
CUDA o LM Studio.

Applicazione, config, dipendenze, Bibbia e DB personali invariati. Modificati
solo documentazione e test documentali. I conteggi dei vecchi milestone restano
evidenze datate; nei README compare il checkpoint portabile corrente, non la
copia dei conteggi storici presentata come attuale.

Verifica di consegna: 300 test Python, OK (sette verifiche opzionali hardware/servizi
saltate); 19 JavaScript e Ruff superati. Tutti i link locali controllati validi;
entrambi i cataloghi coprono i 96 documenti. Nessuna nuova prova GPU/modello
necessaria o dichiarata per questo intervento solo documentale.
