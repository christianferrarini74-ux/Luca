# Mappa grafica della memoria

Data: 2026-10-22. [English](../../memory-graph.md).

## Scopo e utilizzo

Il cruscotto include **Memoria & Sinapsi → Mappa della memoria**. Il vecchio
grafo a righe, che ricavava collegamenti tramite titoli e richiamava i nodi al
clic, è sostituito da una mappa SVG interattiva basata sugli ID del catalogo
della memoria a nodi (V1) e sugli archi diretti realmente presenti in SQLite.

- **Globale**: panorama dei nodi inclusi nei limiti di visualizzazione.
- **Focus · primo grado**: famiglia del focus e famiglie direttamente collegate,
  con archi entranti e uscenti. Senza focus la vista è vuota.
- **Esplora vicinato**: sposta soltanto il centro della mappa sul nodo selezionato;
  il banner distingue questo centro dal focus/lettura effettivi di Luca.
- **Clic o Invio/Spazio**: seleziona e mostra metadati, senza leggere contenuti.
- **Espandi/comprimi famiglia**: mostra/nasconde le parti della stella A–An.
  I collegamenti esterni restano quelli del padre. Il colore rappresenta il
  livello del singolo nodo, non una residenza inventata per tutta la famiglia;
  l'ispettore riporta anche i conteggi dei membri inclusi per livello.
- Trascinamento di nodi o sfondo, rotella, pulsanti zoom e centratura.
- **Cerca nella vista** evidenzia ID/titoli già inclusi, anche nelle famiglie
  compresse; non è una ricerca globale nei contenuti o nei nodi esclusi.
- **Richiama nella giostra** è l'unica azione della mappa che richiede al Core
  di spostare realmente il focus. Rimane disabilitata durante un'operazione.

Verde = VRAM, ambra = RAM, grigio = SSD come livello più alto attualmente
occupato; SSD conserva comunque i dati persistenti. In modalità host compare
un avviso esplicito: il livello VRAM non è memoria GPU fisica. Blu indica il
focus, viola una lettura nel turno. Le rotte locali percorse evidenziano solo
archi esistenti, anche attraversati in senso inverso; gli ingressi globali
sono elencati senza disegnare collegamenti inesistenti. La lista riguarda
l'ultimo turno del navigatore, non una cronologia persistente degli spostamenti.

## Separazione dal motore

`GET /api/graph?mode=global` restituisce metadati; `mode=focus` seleziona il
vicinato del focus, `node_id=123` un centro di esplorazione esplicito.
Query errate restituiscono 400; ID sconosciuti 404. La lettura usa il lock
condiviso con le mutazioni del Core: non richiama nodi, non legge corpi delle
celle, non aggiorna eventi/contatori e non azzera il timer del sonno. Il nuovo endpoint
non sostituisce le preesistenti API del cruscotto che includono estratti.

`graph_view.py` prepara la proiezione; `web/graph.js` gestisce solo disposizione,
selezione e interazioni. La distanza sul disegno non è una nuova metrica di
somiglianza o ragionamento. Nessuna politica della memoria o del modello è
stata trasferita nella GUI. Nessuna nuova dipendenza Python/JavaScript, CDN,
servizio o processo Node necessario all'avvio: sempre `python run_luca.py`.

```yaml
frontend:
  enabled: true
  graph:
    node_limit: 500
    edge_limit: 2000
```

Sono limiti del disegno, non della memoria. Valori ammessi: 1–2000 nodi,
1–10000 archi. La vista favorisce il centro, poi ordina per ID; mostra gli archi
fra i nodi inclusi, entro il tetto. Il banner segnala esplicitamente una vista
parziale e i conteggi. Nessuna paginazione completa o ricerca grafica globale
oltre questi limiti è ancora implementata; per biblioteche grandi servono
ulteriori verifiche. Un limite basso può mostrare una famiglia incompleta.

## Verifiche e consegna

**219 test Python superati**, senza skip, con tokenizer LM Studio e CUDA
reali abilitati; **5 test JavaScript superati** con il runtime Node già
presente, usato soltanto per i test. Coperti ID/titoli duplicati, direzione
degli archi, famiglie, viste parziali, limiti, errori HTTP, assenza di letture
dei corpi, invariabilità di focus/revisioni/eventi/livelli. Un test su CUDA
verifica residenza reale e contatori di trasferimento identici prima/dopo.

```powershell
$env:LUCA_TEST_CUDA='1'
$env:LUCA_TEST_LMSTUDIO='1'
.venv/Scripts/python.exe -m unittest discover -s tests
node --test tests/test_graph_frontend.js
```

Verificata nel browser su server separato con SQLite in memoria: viste globale
e locale, selezione anche da tastiera, espansione, ricerca, zoom/centratura,
richiamo esplicito, temi chiaro/scuro. Durante la verifica è stato corretto
il contrasto del tema scuro. Schermata locale:
`D:\Test\Luca\memory-graph-20261022.png` (dati sintetici, backend host).

Il server di prova viene chiuso a fine verifica; la memoria personale e
l'istanza di Luca già in esecuzione non vengono modificate o riavviate.
Per usare le nuove API, arrestare ordinatamente la vecchia istanza con
**Arresta Luca**, poi avviare `python run_luca.py` e aprire la nuova voce.
Nessuna reinstallazione di pacchetti necessaria.
