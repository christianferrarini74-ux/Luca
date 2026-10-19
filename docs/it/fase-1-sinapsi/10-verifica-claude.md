# Fase 1.10 — Consolidamento dopo la verifica di Claude

Data: 2026-10-19

[English](../../review-hardening.md)

Ambito: verificare la proposta di Claude sull'hardware locale, preservare la
conoscenza personale e correggere costi misurati senza nuove dipendenze né Cesare.
I dati sono sintetici e temporanei, nella directory configurata per i test.

## Identità e topologia del seed

I metadati del seed includono ora un'impronta SHA-256 della mappa canonica
slug-ID e dell'insieme degli archi orientati. L'ordine dei nodi conta perché
determina gli ID; l'ordine della lista degli archi e le sue ripetizioni identiche
non cambiano il grafo. L'impronta è strutturale, non riguarda il testo modificabile
della conoscenza o le aggiunte personali.

I nuovi eventi seed salvano versione e impronta. L'apertura controlla entrambe
e rifiuta strutture incompatibili senza rigenerare o riscrivere il database.
La stessa versione non autorizza più nodi seed riordinati, aggiunti o rimossi.
I nodi personali oltre il seed restano ammessi, indipendentemente dal totale.
Slug duplicati/vuoti ed estremi degli archi sconosciuti sono rifiutati prima
che il caricamento sperimentale esplicito possa cancellare qualcosa.

Per gli eventi precedenti privi d'impronta si verifica lo slug memorizzato a
ciascun ID atteso, senza aggiornare l'evento. Non inventiamo un'impronta storica:
la topologia originaria non è dimostrabile da una biblioteca che può aver
legittimamente acquisito o perso archi. Il controllo legacy delle identità è
quindi meno forte del confronto con un'impronta salvata all'origine.

I test coprono seed invariato, ordine degli archi, aggiunta/rimozione/riordino
dei nodi e modifica degli archi a versione invariata, accettazione/rifiuto legacy
senza scritture, crescita personale e conservazione con seed non valido.
Anche cambiare versione richiede una migrazione esplicita o un database
sperimentale separato: non ordina la sostituzione della conoscenza esistente.
