# Luca: architettura logica

## Regola fondamentale

Luca lavora su celle. Un arco non è mai un'affermazione, un'etichetta o un'unità di verità nascosta: è solo un indirizzo diretto e stabile tra due celle.

LUCA non è un modello linguistico con un grafo allegato. La memoria persistente è il substrato cognitivo; modelli linguistici e sistemi di recupero possono supportarlo, ma non sostituiscono il percorso della conoscenza durevole.

```text
CELL  = contenuto persistente e stato cognitivo
EDGE  = source_id : target_id
```

Le celle possono rappresentare un concetto (`fuoco`), un concetto-relazione (`scalda`), un'esperienza, una domanda, un'ipotesi, un'evidenza o una conclusione. Il percorso `fuoco → scalda → ferro` può essere attivato, ispezionato, rinforzato, contestato o riutilizzato senza aggiungere semantica agli archi.

## Memoria diretta

Ogni arco esiste in due ordinamenti fisici:

```text
indice diretto  [source_id, target_id]  risponde a A:*
indice inverso  [target_id, source_id]  risponde a *:B
```

Questa è la navigazione locale garantita di Luca. Scopre materiale correlato attraverso celle condivise e percorsi ripetuti, senza una ricerca associativa o vettoriale.

## Livelli di memoria

```text
SSD
  Cervello persistente completo: celle, archi, indici durevoli, modifiche append-only.

RAM
  Contesto corrente: celle richieste, vicinato topologico, regioni in cache,
  stato del coordinatore e modifiche pendenti.

VRAM
  Working set ristretto per un pensiero: ID, archi, stato numerico compatto e attivazioni.
```

L'SSD è autorevole. La RAM è una cache operativa mutabile. La VRAM contiene snapshot eliminabili; una GPU non può fare commit nel cervello.

## Ciclo del pensiero

1. Un trigger seleziona celle-seme e un obiettivo esplicito.
2. La RAM carica i semi e il vicinato `A:*` / `*:B`.
3. Il coordinatore espande una frontiera delimitata e assegna punteggi ai candidati.
4. Un focus più piccolo viene promosso in VRAM quando esiste una GPU.
5. I risultati tornano come proposte con traccia, non come scritture dirette.
6. Un solo consolidatore valida, unisce e persiste le modifiche accettate.

Ogni pensiero ha budget fissi: profondità, celle RAM, archi RAM, celle VRAM e tempo. I budget sono sia limiti ingegneristici sia disciplina cognitiva.

## Ruoli di calcolo

L'implementazione CPU definisce la semantica di riferimento. Un backend GPU può accelerare propagazione, scoring e ricerca associativa solo dopo test di parità con la CPU.

Con più GPU, il coordinatore può dividere rami indipendenti dello stesso pensiero. Ogni ramo riceve uno snapshot in sola lettura e un budget proprio. I worker restituiscono candidati, evidenze e tracce; il consolidatore resta l'unico scrittore.

## Salti associativi: livello futuro

L'indice associativo futuro non è un database di embedding testuali. Indicizza indirizzi compatti che rimandano alle celle. Può proporre candidati lontani; Luca deve verificarli caricando il vicinato reale del grafo.

Due regioni completamente scollegate, senza celle condivise, co-attivazione, regolarità osservata o ponte esterno, non contengono segnali per inferire somiglianza. È una condizione da testare, non una lacuna da nascondere.
