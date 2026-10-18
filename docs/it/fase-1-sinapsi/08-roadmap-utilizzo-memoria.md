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
