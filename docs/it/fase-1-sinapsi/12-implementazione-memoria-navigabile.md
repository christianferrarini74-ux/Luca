# Fase 1.11 — Esecuzione e accettazione

[English](../../phase-1-11-implementation.md)

Ambito: realizzare la [specifica confermata](11-memoria-sinaptica-riorganizzabile.md),
non importazione libri, distillazione o integrazione Cesare. I test automatici e
gli script di sviluppo non utilizzano né riscrivono i database personali.

1. Fondamenta persistenti: famiglia a stella esplicita, identità canonica,
   modifiche transazionali, revisioni, alias correnti e ricerca globale.
   Verifiche: rollback, rinomina, riavvio e compatibilità dei nodi ordinari.
2. Rubrica rapida completa di primo grado, indipendente dalla residenza dei
   contenuti. Verifiche: entranti/uscenti, continuità familiare e invalidazione
   delle copie obsolete, anche quando fallisce un'allocazione GPU. Nessun taglio
   silenzioso dei riferimenti di navigazione.
3. Navigazione LLM: protocollo limitato cerca/apri/rispondi; il Core verifica ID,
   revisioni e percorsi, senza sostituirsi nella scelta semantica. La modalità
   precedente a regole resta disponibile come configurazione esplicita di test.
4. Manutenzione: soglie configurabili, piani manuali con conferma e avvio automatico
   in inattività, raggruppamenti orientati, verificabili e reversibili. Verifiche:
   rotte originali, piani obsoleti, rollback e riduzione del grado locale.
5. Integrazione: visibilità API/cruscotto, test deterministici completi, suite
   portabile e verifiche CUDA reali opzionali. Registrare qui e nei README bilingui
   risultati e limiti residui; commit dei passaggi verificati.

Stato implementativo e risultati vengono registrati di seguito durante il lavoro.

Checkpoint fondamenta: implementati famiglie canoniche, rubrica completa,
migrazione additiva revisioni/catalogo, modifiche atomiche e slot host/device
consapevoli della revisione. Suite portabile: 116 test, 3 verifiche hardware
saltate. Il vecchio test che equiparava primo grado e contenuti precaricati ora
verifica separatamente le due proprietà. Nessun database personale aperto.
