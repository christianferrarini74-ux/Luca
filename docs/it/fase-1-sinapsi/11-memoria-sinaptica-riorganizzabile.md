# Fase 1.11 — Memoria sinaptica navigabile e riorganizzabile

Data: 2026-10-20

[English](../../bounded-synaptic-memory-design.md)

Stato: sintesi progettuale della discussione con Christian, da usare per definire
la prossima roadmap. Questo documento non descrive funzionalità già implementate
e non autorizza da solo modifiche al grafo personale.

## 1. Obiettivo e confini

Luca deve conservare conoscenza completa, collegata e progressivamente crescente,
rendendola utilizzabile da un LLM con risorse e contesto finiti. La crescita della
biblioteca non deve richiedere di inserire tutta la biblioteca nel prompt, né di
ridurla obbligatoriamente a riassunti.

Luca è progettato come sistema autonomo. Le sue strutture non devono derivare da
vincoli di Cesare o di un altro programma. Qualsiasi integrazione futura sarà
valutata separatamente e non determina le decisioni di questo documento.

Il riferimento al cervello e al suo “sonno” è una metafora funzionale: indica una
fase di manutenzione della memoria, non una riproduzione biologica dimostrata.

## 2. Il punto di partenza: il libro e il suo indice

Il PDF originale resta una fonte persistente e riconoscibile. La struttura
editoriale è il primo strumento di organizzazione, prima di inventare suddivisioni
arbitrarie o associazioni automatiche.

Il nodo d'ingresso del libro contiene titolo, argomento, provenienza e indice.
Ogni voce indirizza un nodo di capitolo o argomento; un capitolo può a sua volta
contenere un sottoindice verso sezioni e sottosezioni. Ordine, titoli e pagine
appartengono ai dati dei nodi e dell'indice. Gli archi restano indirizzi orientati
senza un proprio contenuto semantico.

Questa gerarchia non limita la memoria a un albero chiuso: un nodo può collegarsi
a conoscenze di altri libri e ad altri ingressi tematici. Distinguere una stessa
parola da un concetto realmente condiviso rimane essenziale: non si fondono
automaticamente conoscenze soltanto perché hanno lo stesso titolo.

Individuare una voce nota mediante un indirizzo non richiede di scandire il libro.
Interpretare una domanda libera e scegliere l'ingresso corretto è invece un
problema distinto, che richiede valutazione e può fallire.

## 3. Tre piani da non confondere

| Piano | Che cosa rappresenta | Che cosa non implica |
| --- | --- | --- |
| Conoscenza persistente | Fonti, contenuti completi, nodi e collegamenti conservati su SSD. | Non deve essere tutta residente o tutta letta. |
| Residenza fisica | Payload effettivamente conservati nei livelli SSD/RAM/VRAM. | Un nodo in VRAM non è automaticamente nel prompt. |
| Esposizione all'LLM | Contenuti e alternative di navigazione esaminati nel contesto corrente. | L'LLM non conosce automaticamente ciò che non ha esaminato. |

La giostra governa la residenza e il ricambio dei payload. La navigazione governa
quale conoscenza aprire. La costruzione del prompt governa quanto esporre in una
singola elaborazione. Sono responsabilità coordinate, non equivalenti.

In particolare, un libro può rimanere quasi interamente su SSD mentre indice e
indirizzi rendono raggiungibili i suoi contenuti. Il caricamento di un capitolo
ha comunque un costo reale di lettura e trasferimento, proporzionato al payload.

## 4. Chi sceglie il percorso

Il ruolo desiderato dell'LLM è scegliere il prossimo nodo da aprire, sulla base
della domanda, del focus e delle alternative disponibili. Il Core verifica che
indirizzo e operazione siano validi, esegue il richiamo e applica le politiche di
risorse; non deve sostituire la propria preferenza semantica alla scelta dell'LLM.

La stessa distinzione vale per la riorganizzazione: l'LLM può proporre titoli,
confini e raggruppamenti. Il Core controlla integrità strutturale e applicazione.
Questi controlli non dimostrano, da soli, che il raggruppamento sia semanticamente
buono: inizialmente serve anche la revisione umana.

L'autonomia di navigazione non autorizza esecuzione arbitraria, accesso a file
estranei o modifiche dirette e non validate della memoria.

## 5. Il requisito sugli archi e la difficoltà di scala

Un nodo B deve rendere disponibili tutti i suoi archi attivi con prefisso B:*
e suffisso *:B. Non basta il sottoinsieme che entra nel precaricamento dei nodi
vicini. La capacità della giostra non deve amputare la rubrica del focus.

Esiste però un vincolo informativo: non si possono mostrare arbitrariamente
molti indirizzi e descrizioni in un contesto finito. La consultazione paginata è
una soluzione possibile, ma non è la direzione principale scelta in questa
discussione. La proposta qui è organizzare la memoria in modo che ogni scelta
locale rimanga abbastanza piccola e comprensibile da essere esposta per intero.

Raggiungibilità completa e lettura esaustiva restano diverse: poter arrivare a
tutti i nodi non garantisce che l'LLM scelga il percorso corretto o li esamini tutti.

## 6. Limite morbido delle connessioni

L'ipotesi di lavoro di Christian è una soglia di 100 connessioni incidenti, fra
entranti e uscenti. Al 101° collegamento il nodo viene segnalato per un riordino
locale che lo riporti, per esempio, a non più di 90.

Sono parametri sperimentali, non valori già approvati per il codice. Il margine
fra soglia di intervento e obiettivo evita di riorganizzare a ogni nuova aggiunta.
Il limite è morbido: l'acquisizione può superarlo temporaneamente mentre il nodo
attende una finestra di manutenzione.

Per allinearsi ai contatori attuali, una definizione candidata è grado entrante
più grado uscente. Un auto-collegamento conterebbe quindi due incidenze: questa
convenzione va dichiarata e confermata, non lasciata implicita.

Raggruppare dodici archi diretti in una sola connessione a un intermediario
riduce, nell'esempio semplice, un grado 101 a 90. Anche l'intermediario consuma
una connessione sul nodo padre; il suo collegamento al padre consuma capacità
nel proprio budget. Collegamenti inversi espliciti o trasversali consumano altra
capacità. Non basta contare soltanto le nuove diramazioni.

## 7. Raggruppare senza falsificare le relazioni

Il raggruppamento inserisce nodi intermedi di orientamento con titoli e brevi
descrizioni significative. Il percorso diretto viene sostituito da un percorso
attraverso il gruppo: la memoria resta raggiungibile ma la distanza può crescere.
Un gruppo chiamato “Termodinamica” può aiutare a scegliere; “Gruppo 7” da solo no.

Questa è una precisazione decisiva: non possiamo mantenere tutti i vecchi archi
come connessioni attive del focus e contemporaneamente dichiararne ridotto il
grado. Le connessioni precedenti devono essere reindirizzate, con provenienza e
mappatura conservate separatamente per audit, riferimenti storici e ripristino.

I nodi di orientamento devono essere distinguibili dai nodi che affermano
conoscenza. Un cammino attraverso un gruppo non equivale a una nuova relazione
diretta fra ogni coppia dei suoi membri. Raggruppare collegamenti entranti e
uscenti richiede di preservare direzione e appartenenza delle rotte originali,
senza creare scorciatoie o combinazioni semantiche non autorizzate.

Anche i nodi intermedi rispettano le soglie. Il riordino deve evitare sia di
spostare l'hub un livello più in basso sia di costruire catene troppo profonde.
Il compromesso da misurare è ampiezza locale, profondità e comprensibilità delle
scelte, non soltanto il numero finale di archi.

## 8. Limitare anche l'informazione del nodo

Un nodo con poche connessioni può comunque contenere un capitolo enorme. Serve
quindi una soglia separata per il contenuto, con un obiettivo di riduzione che
lasci margine, come per gli archi.

La dimensione può essere misurata in byte del payload e rispetto al budget di
esposizione; nessuna di queste misure quantifica da sola la complessità semantica.
Non abbiamo ancora stabilito valori o una formula unica. I limiti fisici restano
rigidi: una soglia cognitiva morbida non permette di allocare oltre la VRAM
disponibile. Un payload non caricabile deve restare persistente e attendere
suddivisione o una decisione esplicita, senza fingere che sia stato caricato.

Quando il contenuto è eccessivo, il nodo mantiene la propria identità logica e
diventa ingresso a un sottoindice; le parti complete passano in nodi figli.
L'originale e la sua versione restano conservati su SSD: non occorre mantenere
anche l'intero capitolo duplicato nel payload attivo del padre.

Le divisioni devono seguire unità comprensibili e preservare definizioni,
condizioni, esempi e rimandi necessari. Un numero di caratteri determina che
occorre intervenire, non stabilisce automaticamente il confine corretto.

## 9. Distillare la mappa, non eliminare la conoscenza

La distillazione proposta è organizzativa: identifica sottoargomenti e produce
titoli, brevi descrizioni e sottoindici utili alla navigazione. Non è il riassunto
che rimane al posto della fonte.

Il contenuto originale viene distribuito integralmente fra i nodi figli. Ogni
porzione mantiene fonte, ordine e posizione nel testo di riferimento. I puntatori
persistenti alla fonte non sostituiscono il contenuto fisico quando il nodo viene
caricato: il payload necessario deve essere realmente materializzato.

Per il testo estratto deve essere verificabile la copertura completa e, dove
possibile, la ricostruzione ordinata. Eventuali sovrapposizioni necessarie vanno
segnalate; non devono nascondere lacune. La correttezza dell'estrazione dal PDF,
soprattutto per scansioni, tabelle, immagini e formule, è una verifica precedente
e distinta. Conservare perfettamente un testo estratto male non conserva tutto
il significato del libro.

Descrizioni generate e testo della fonte devono rimanere distinguibili. La mappa
può essere migliorata senza riscrivere ciò che l'autore ha effettivamente detto.

## 10. Contenuto e connessioni condividono il contesto

I limiti non si esauriscono in “100 archi” e “un certo numero di byte”. Una singola
elaborazione deve contenere istruzioni, domanda, stato del compito, storia utile,
contenuto esposto, rubrica completa del focus e riserva per la risposta.

I titoli e le descrizioni hanno un costo: cento archi con descrizioni lunghe
possono essere troppi anche quando il testo del nodo è breve. Perciò la fattibilità
dell'esposizione deve avere un proprio controllo complessivo. Il numero massimo
di archi è un tetto strutturale, non un obiettivo da raggiungere sempre.

Lo sforamento temporaneo del grafo non autorizza il taglio silenzioso del prompt.
Se il focus non è esponibile integralmente secondo il contratto scelto, occorre
prima riorganizzarlo o sospenderne esplicitamente l'apertura. La politica precisa
è una decisione da prendere nella roadmap. Non possiamo garantire insieme
sforamento illimitato, scelta immediata e visione integrale in un prompt finito.

Le due trasformazioni si influenzano: suddividere il testo crea nuovi archi;
raggruppare archi crea nuovi indici e contenuti descrittivi. Il riordino va quindi
validato congiuntamente su connessioni, contenuto e contesto, non come due
procedure indipendenti che possono far sforare continuamente l'altra soglia.

## 11. Il “sonno”: manutenzione locale, non ricostruzione globale

La manutenzione raccoglie i nodi oltre soglia e prepara interventi piccoli e
puntuali. Può essere avviata su comando, in una fase concordata o durante
inattività effettiva. Il funzionamento automatico non è ancora una decisione
implementativa approvata.

La sequenza logica è: rilevare lo sforamento; accodare il nodo senza duplicare
il lavoro; proporre raggruppamento o suddivisione; verificare contenuti e rotte;
pubblicare la nuova organizzazione; ricontrollare i nodi coinvolti.

Il processo deve essere limitato per lavoro e risorse, interrompibile e
riprendibile, senza oscillazioni continue. Se i dati cambiano dopo la proposta,
questa va rivalidata. Una mancata manutenzione non deve trasformarsi in crescita
illimitata nascosta: servono diagnostica e una politica esplicita di pressione.

La pubblicazione deve rendere visibile una versione coerente del grafo. Una
transazione SQLite non rende automaticamente atomiche anche le allocazioni GPU:
lettori in corso, payload residenti, cache e riferimenti del compito richiedono
una strategia coordinata di versionamento e invalidazione. Errori o interruzioni
devono lasciare recuperabile l'assetto precedente, non una struttura a metà.

Anche il riordinatore lavora con contesto finito: non deve richiedere di leggere
in un solo prompt tutto ciò che il sistema cerca di rendere gestibile. Può usare
prima indice e confini della fonte, poi esaminare porzioni successive con riferimenti
espliciti. Se non individua una suddivisione affidabile, deve lasciare una proposta
in sospeso o chiedere revisione, non forzare un taglio soltanto per rispettare una soglia.

## 12. Invarianti da usare come criteri di accettazione

- Nessuna perdita silenziosa di contenuto, fonti o collegamenti.
- Tutte le alternative attive del focus sono disponibili, non soltanto un top-K.
- La riorganizzazione cambia i percorsi, non inventa nuovi fatti fra i membri.
- Identità e riferimenti preesistenti restano risolvibili o esplicitamente migrati.
- Anche i nuovi nodi rispettano i budget e la profondità non cresce senza controllo.
- La presenza in VRAM è reale; l'esposizione all'LLM è una decisione distinta.
- Nessun riordino viene applicato parzialmente a una conversazione in corso.
- Il cruscotto rende visibili stato, scelte e manutenzione; non contiene la logica.
- Non si impongono nuovi framework per convenienza: ogni dipendenza va motivata.

## 13. Che cosa esiste e che cosa manca

Il codice attuale dispone di persistenza SQLite, indirizzi orientati, giostra
fisica CUDA, budget dei payload e del contesto, diagnostica, planner di richiamo
e controlli sul seed. Il milestone precedente registra 105 test superati, anche
con CUDA reale; questo report non costituisce una nuova esecuzione di quei test.

Non implementa ancora il modello descritto qui. In particolare, il richiamo
limita il recupero degli archi a `max(32, vram_capacity * 4)` per direzione e il
precaricamento dei vicini alla capacità del livello attivo. Il planner è ancora
ibrido e spesso sceglie mediante regole, non tramite una navigazione autonoma
dell'LLM su tutte le alternative.

Mancano importazione del libro guidata dall'indice, contratto di rubrica completa,
soglie di riorganizzazione, nodi intermedi gestiti, suddivisione conservativa,
coda di manutenzione e pubblicazione versionata delle trasformazioni. L'uso di
un PDF concreto richiederà inoltre la scelta e la verifica dell'estrazione,
senza installare automaticamente dipendenze.

## 14. Decisioni da chiudere prima della roadmap esecutiva

1. Soglie iniziali e margini per archi e contenuto; convenzione di conteggio.
2. Formato e budget delle descrizioni della rubrica, oltre ai soli ID.
3. Rappresentazione dei nodi di orientamento e delle rotte originali conservate.
4. Politica sul focus temporaneamente oltre il budget di esposizione.
5. Contratto operativo con cui l'LLM consulta, apre, torna indietro e si arresta.
6. Criteri di raggruppamento e divisione, con revisione umana iniziale.
7. Trigger, limiti e approvazione della manutenzione; gestione delle versioni.
8. Un primo libro/capitolo scelto insieme, con domande e riferimenti verificabili.

Queste sono decisioni progettuali, non una sequenza di sviluppo già autorizzata.
La roadmap successiva dovrà trasformarle in esperimenti e criteri misurabili:
copertura, correttezza delle rotte, scelta dell'LLM, contesto consumato, profondità,
latenza, costo di manutenzione e ripristino dopo errore.

## 15. Conclusione

La proposta chiude il problema della scala attraverso la riorganizzazione della
struttura, non promettendo un contesto infinito: conoscenza completa su supporti
persistenti; unità informative e scelte locali controllabili; navigazione guidata
dall'LLM; manutenzione che distribuisce gli eccessi senza perdere la fonte.

Il libro offre la prima organizzazione. I collegamenti fra fonti la estendono.
La giostra porta vicino ciò che serve. Il “sonno” mantiene percorribile la rete.
La distillazione costruisce la segnaletica, non sostituisce la conoscenza.

Questa è un'ipotesi architetturale coerente da verificare, non una dimostrazione
che ogni riordino migliori il richiamo. La prova decisiva sarà mantenere contenuti
e percorsi corretti mentre cresce la biblioteca e cambiano le domande.

## Riferimenti della ricerca precedente

- [PageIndex: navigazione dell'albero documentale](https://docs.pageindex.ai/tutorials/tree-search/llm): utile per la struttura; l'esempio base espone l'albero nel prompt.
- [MemGPT](https://shishirpatil.github.io/publications/memgpt-2023.pdf): separazione fra memoria esterna e contesto; paginazione e limiti dell'esplorazione effettiva.
- [GraphWalk](https://arxiv.org/html/2604.01610v1): esplorazione tramite strumenti; non dimostra la gestione di un hub enorme esponendone tutti i vicini.
- [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview): consultazione parziale e gestione esterna dei risultati, come meccanismi adiacenti.

Sono riferimenti parziali, non dipendenze adottate né prove di equivalenza con Luca.
