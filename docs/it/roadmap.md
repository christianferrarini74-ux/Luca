# LUCA: roadmap di validazione

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

La roadmap è ordinata secondo le evidenze. Una fase successiva non è giustificata solo perché la precedente è stata codificata.

## 1. Dimostratore di memoria conversazionale

Costruire un dialogo persistente e ristretto in cui Luca risponda a domande semplici, riceva un fatto, lo conservi dopo il riavvio, mantenga un breve contesto, rifiuti affermazioni sconosciute e registri una correzione con provenienza.

**Evidenza:** trascrizioni multi-turno ripetibili e test con set di valutazione separato.

## 2. Memory Fabric nativo

Sostituire l'ipotesi del solo database con regioni su SSD, budget di cache RAM, decisioni esplicite di caricamento/espulsione, aggiornamenti durevoli append-only e focus VRAM simulato.

## 3. Esperimento di indirizzo associativo

Verificare se topologia, co-attivazione e ruoli dei percorsi recuperano candidati lontani utili oltre la traversata diretta `A:*` e `*:B`, riportando anche il tasso di falsi salti.

## 4–5. Parità GPU singola e rami multi-GPU

Portare una singola operazione provata sulla CPU su GPU senza cambiarne traccia o risultato; poi schedulare rami indipendenti con budget VRAM separati e un solo consolidatore.

## 6. Memory Fabric distribuito

Separare memoria persistente globale e nodi di calcolo. I nodi caricano regioni versionate, calcolano localmente, restituiscono proposte e fanno commit attraverso un percorso controllato.

## Soglia di presentazione

Luca sarà presentabile come concept funzionante quando dimostrerà end-to-end e in modo riproducibile:

```text
insegnare → persistere → riavviare → recuperare → contestualizzare → correggere → spiegare
```

La presentazione deve dichiarare apertamente i limiti e invitare a una valutazione tecnica seria, non rivendicare parità con gli LLM frontier.
