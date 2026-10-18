# Fase 1.08 — Roadmap per l'utilizzo della memoria, punti 1–5

Data: 2026-10-19. Ambito: solo Luca; integrazione con Cesare rinviata.

[English](../../memory-development-roadmap.md)

1. Rendere eseguibile il dialogo dei sommergibili: riferimento ai mezzi gialli,
   cambio laterale di animale, enumerazione della famiglia, accenti, parafrasi,
   esclusioni e argomenti sconosciuti.
2. Introdurre un pianificatore con baseline deterministica e proposte LLM
   facoltative e limitate. Il Core verifica ID e percorsi; condividere vicini
   nel grafo non dimostra pertinenza semantica. Gli archi restano indirizzi puri.
3. Distinguere precaricamento, apertura, attraversamento ed esposizione nella
   risposta. L'attività recente ha durata limitata; aprire un hub non rinforza
   tutti i nodi aperti in passato. Conservare conoscenza SSD e invarianti dei livelli.
4. Limitare contesto e cache anche per dimensione. Conservare l'identità del
   documento e permettere l'accesso alle sezioni. Separare metadati d'uso dal
   contenuto evitando reindicizzazioni al richiamo. Limitare l'intera richiesta
   al modello: cronologia, domanda, istruzioni e riserva per la risposta.
5. Conservare obiettivo, vincoli, decisioni e focus riprendibile separatamente
   dai cluster. Le modifiche del compito sono esplicite, limitate e visibili nell'API.

Accettazione: test deterministici e planner simulato, rifiuto di piani invalidi,
oblio e cache piccole, contenuti grandi, ripresa fra cluster scollegati,
contratti HTTP e prova reale con modello locale. Documentare i limiti e separare
prompt sperimentali e conversazione libera. Acquisizione e Cesare sono esclusi.

## Punti 1–3 implementati

Il dialogo di riferimento conserva gli attributi dell'oggetto, cambia membro
lateralmente e apre la famiglia per enumerarla. Il planner ibrido accetta
proposte del modello soltanto fra candidati verificati sul grafo e si astiene
quando restano alternative indistinguibili. Le negazioni sono delimitate per
proposizione; `Perché` e `Perche` sono normalizzati coerentemente. È una baseline,
non una comprensione semantica senza limiti.

L'attività distingue precaricamento, apertura, attraversamento, associazione,
esposizione e retrocessione. La priorità recente scade entro una finestra
limitata. Rinforzano gli archi solo attraversamenti effettivi o collegamenti che
giustificano il richiamo scelto. Esposizione significa contenuto fornito per una
risposta riuscita, non prova di utilizzo corretto da parte del modello.
La tabella SQLite `node_usage` conserva l'utilizzo separato dal testo indicizzato.

## Punto 4 implementato

`runtime.context_budget` configura l'intera richiesta e i sotto-budget di memoria
e cronologia. L'accounting usa byte UTF-8 in modo conservativo: non è il tokenizer
del provider né una garanzia per template arbitrari. La finestra va impostata
entro quella reale del modello sul server. Le domande troppo grandi sono
rifiutate, non tagliate silenziosamente.
VRAM e RAM limitano anche il payload serializzato conservato (`vram_bytes`,
`ram_bytes`), non RSS del processo o allocazione fisica GPU. I nodi troppo grandi
hanno viste parziali in cache che non possono sovrascrivere la conoscenza SSD.
Caricare una sorgente completa per estrarne una sezione può ancora allocarla
temporaneamente.

I nodi supportano `summary` e `sections` con `key`, `title`, `content`.
Il backend verifica `/api/section` mantenendo l'ID del documento come focus ed
esponendo la sezione scelta. Gli estratti sono marcati come parziali. La GUI
mostra budget e controlli per le sezioni, senza eseguire logica di memoria.
Contenuto sorgente e indice non cambiano quando si aggiorna soltanto l'utilizzo.
