# Fase 1.11 — Memoria sinaptica navigabile e riorganizzabile

Data: 2026-10-20

[English](../../bounded-synaptic-memory-design.md)

Stato: sintesi progettuale della discussione con Christian, da usare per definire
la prossima roadmap. Questo documento non descrive funzionalità già implementate
e non autorizza da solo modifiche al grafo personale.

Integrazione del 2026-10-20: dimensione informativa in parole, oppure in token
quando il conteggio esatto è semplice; continuità dell'intera rubrica del nodo
originale durante la lettura dei suoi frammenti (§8 e §10).

Precisazione successiva di Christian: la prossima fase riguarda soltanto
navigazione delle sinapsi e gestione degli archi, assumendo nodi già conformi
per contenuto. La distillazione e la suddivisione dei testi (§8–9) sono un sistema
separato e rinviato. Sono fissati limite superiore 50 e obiettivo inferiore 45,
entrambi nel file di configurazione; rubrica esposta con soli ID e titolo.
Le risposte ai punti del §14 sono aggiornate di conseguenza.

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

La stessa distinzione vale per la riorganizzazione degli archi: l'LLM può proporre
titoli e raggruppamenti. Il Core controlla integrità strutturale e applicazione.
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

Christian ha scelto un limite iniziale di 50 connessioni incidenti, sommando
prefissi e suffissi, e un obiettivo di riordino di 45. Sono parametri modificabili
nel file di configurazione, non costanti inserite nel codice. La precedente
ipotesi 100/90 è superata. Il margine fra intervento e obiettivo evita di
riorganizzare a ogni nuova aggiunta.
Il limite è morbido: l'acquisizione può superarlo temporaneamente mentre il nodo
attende una finestra di manutenzione.

Il riordino automatico riguarda solo nodi oltre 50, durante il non utilizzo
dell'LLM. Il comando manuale richiede conferma e opera sui nodi selezionati,
portandoli al limite inferiore anche se non hanno superato quello superiore;
un nodo già entro l'obiettivo non richiede compressione. La selezione automatica
deve ricontrollare lo sforamento al momento di intervenire.

I nomi tecnici delle chiavi saranno fissati nell'implementazione. La validazione
richiederà valori interi positivi e obiettivo inferiore al limite. Non si aggiungono
ora chiavi inerti al config.yaml di un runtime che non implementa ancora il riordino.

Per allinearsi ai contatori attuali, una definizione candidata è grado entrante
più grado uscente. Un auto-collegamento conterebbe quindi due incidenze: questa
convenzione va dichiarata e confermata, non lasciata implicita.

Raggruppare sette archi diretti in una sola connessione a un intermediario
riduce, nell'esempio semplice, un grado 51 a 45. Anche l'intermediario consuma
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

Contesto progettuale per una fase separata: non è lavoro incluso nella prossima
roadmap di navigazione. Per quest'ultima si assumono nodi con contenuti già adeguati.

Un nodo con poche connessioni può comunque contenere un capitolo enorme. Serve
quindi una soglia separata per il contenuto, con un obiettivo di riduzione che
lasci margine, come per gli archi.

La misura operativa del contenuto è il numero di parole. Un conteggio iniziale
semplice e riproducibile può contare le sequenze non vuote separate da spazi
bianchi, senza un analizzatore linguistico. Se il tokenizer esatto del modello
è già disponibile con costo e integrazione trascurabili, si preferiscono i
token. Non introduciamo un framework o chiamate remote soltanto per contarli.

Le parole sono una misura pratica per decidere quando suddividere, non una
garanzia esatta di occupazione del prompt. Lingua, codice, formule e tokenizzazione
impediscono una conversione fissa valida sempre. Le soglie andranno calibrate sul
modello e sul tipo di contenuto; il controllo finale del contesto resta distinto.
Né parole né token misurano da soli la complessità semantica.

I byte rimangono la misura delle allocazioni e dei trasferimenti fisici, non
la misura primaria della dimensione informativa. Non abbiamo ancora stabilito
le soglie in parole/token. Una soglia organizzativa morbida non permette di
allocare oltre la VRAM disponibile: un payload non caricabile resta persistente
in attesa di suddivisione o di una decisione esplicita, senza fingere il caricamento.

Quando il contenuto è eccessivo, il nodo mantiene la propria identità logica e
diventa ingresso a un sottoindice; le parti complete passano in nodi figli.
L'originale e la sua versione restano conservati su SSD: non occorre mantenere
anche l'intero capitolo duplicato nel payload attivo del padre.

Le divisioni devono seguire unità comprensibili e preservare definizioni,
condizioni, esempi e rimandi necessari. Il conteggio di parole/token segnala che
occorre intervenire, non stabilisce automaticamente il confine corretto.

### Continuità sinaptica durante la suddivisione

Se A viene suddiviso in A1, A2, A3, A4 e A5, aprire una qualsiasi parte deve
conservare disponibili tutti gli archi attivi di A, entranti e uscenti, oltre
agli eventuali collegamenti propri della parte. La navigazione tra le parti
rimane disponibile e la parte corrente è identificata. Non è sufficiente un
arco per tornare al padre: l'LLM non deve abbandonare il dettaglio per ritrovare
la mappa originale. A diventa l'ancora della conoscenza; Ai è il focus di lettura.

Il requisito è disponibilità completa in ogni frammento, non necessariamente
duplicazione fisica degli stessi archi. La proposta implementativa da valutare
è una rubrica condivisa, riferita dall'intera famiglia di suddivisione, più i
collegamenti locali. Ogni parte ne materializza la vista completa quando viene
aperta. I contenuti delle altre parti non devono essere caricati per questo.

Direzione e origine dei collegamenti restano esplicite: un arco A:B ereditato
per la navigazione non viene presentato come una nuova affermazione A1:B.
Il Core dovrà validare la scelta rispetto alla rubrica effettiva del contesto
di lettura, non soltanto rispetto agli archi fisicamente intestati ad Ai.
Gli archi identici sono esposti una volta sola, conservando la loro identità;
una voce diretta alla parte già aperta è riconoscibile come tale.

L'ereditarietà riguarda la relazione esplicita di suddivisione, non qualunque
collegamento del grafo. Se anche A1 viene suddiviso, le nuove parti non devono
perdere l'ancora A: ereditano la continuità della famiglia e tutte le connessioni
dei livelli di suddivisione. Una modifica della rubrica condivisa
deve aggiornare coerentemente le viste delle parti, senza copie divergenti.
Versionamento e rappresentazione concreta sono decisioni per la roadmap.

## 9. Distillare la mappa, non eliminare la conoscenza

Sistema di generazione/distillazione dei contenuti rinviato, distinto dal
raggruppamento degli archi durante il “sonno” previsto nella fase corrente.

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

I limiti non si esauriscono in “50 archi” e “un certo numero di parole/token”. Una singola
elaborazione deve contenere istruzioni, domanda, stato del compito, storia utile,
contenuto esposto, rubrica completa del focus e riserva per la risposta.

Il formato scelto per la rubrica è ID e titolo, senza descrizioni generate
aggiuntive. Anche questi titoli hanno un costo. Perciò la fattibilità
dell'esposizione deve avere un proprio controllo complessivo. Il numero massimo
di archi è un tetto strutturale, non un obiettivo da raggiungere sempre.

Per un frammento conta la rubrica effettivamente esposta: archi ereditati dalla
famiglia, archi locali e navigazione delle parti, senza duplicare lo stesso arco.
Memorizzare la rubrica una volta sola risparmia storage, non il contesto necessario
per mostrarla. Il solo grado fisico di Ai non basta a certificare il rispetto
della soglia; anche la vista combinata deve essere controllata. Lo stesso vale
per suddivisioni su più livelli. Per l'informazione si contano separatamente le
parole del contenuto e quelle dei descrittori, verificando poi l'intero prompt.
Non si risolve uno sforamento nascondendo arbitrariamente gli archi ereditati.

Lo sforamento temporaneo del grafo non autorizza il taglio silenzioso del prompt.
Se il focus non è esponibile integralmente secondo il contratto scelto, occorre
segnalare la condizione: non è stata scelta una politica di riorganizzazione
immediata, sospensione o compressione automatica della conversazione. Per ora si
misura il contesto complessivo, senza trasformare questo tema in un requisito
bloccante per la navigazione. Non possiamo garantire insieme
sforamento illimitato, scelta immediata e visione integrale in un prompt finito.

Nel sistema complessivo, la futura suddivisione del testo potrà creare nuovi
archi, mentre il raggruppamento degli archi crea nuovi indici. Per la fase corrente
si assume però contenuto già adeguato: si verificano i collegamenti e il costo
della loro esposizione senza introdurre ora una procedura di suddivisione del testo.

## 11. Il “sonno”: manutenzione locale, non ricostruzione globale

La manutenzione della fase corrente raggruppa archi in famiglie e genera i relativi
nodi intermedi: non distilla e non suddivide il contenuto dei nodi. Sono previste
due modalità: comando manuale con conferma sui nodi selezionati, oppure esecuzione
automatica durante il non utilizzo dell'LLM soltanto sui nodi oltre il limite
superiore configurato. Entrambe mirano al limite inferiore configurato.

La sequenza logica è: rilevare lo sforamento; accodare il nodo senza duplicare
il lavoro; proporre il raggruppamento degli archi; verificare famiglie e rotte;
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

Anche il riordinatore lavora con contesto finito. In questa fase organizza le
connessioni tramite ID e titoli, senza dover distillare il contenuto dei libri.
Se non individua famiglie affidabili, lascia una proposta in sospeso o richiede
revisione, senza cancellare archi o inventare gruppi soltanto per rispettare una soglia.

## 12. Invarianti da usare come criteri di accettazione

- Nessuna perdita silenziosa di contenuto, fonti o collegamenti.
- Tutte le alternative attive del focus sono disponibili, non soltanto un top-K.
- La riorganizzazione cambia i percorsi, non inventa nuovi fatti fra i membri.
- Identità e riferimenti preesistenti restano risolvibili o esplicitamente migrati.
- Ogni parte mantiene l'intera rubrica del nodo suddiviso anche mentre è il focus di lettura.
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

L'attuale contabilità del prompt usa byte UTF-8 conservativi: non è già il
conteggio in parole o il tokenizer esatto previsto da questa integrazione.

Non implementa ancora il modello descritto qui. In particolare, il richiamo
limita il recupero degli archi a `max(32, vram_capacity * 4)` per direzione e il
precaricamento dei vicini alla capacità del livello attivo. Il planner è ancora
ibrido e spesso sceglie mediante regole, non tramite una navigazione autonoma
dell'LLM su tutte le alternative.

Nel perimetro immediato mancano contratto di rubrica completa, navigazione guidata
dall'LLM, soglie configurabili, nodi intermedi gestiti, coda di manutenzione e
pubblicazione coerente delle trasformazioni. Importazione dei libri, estrazione
PDF e distillazione/suddivisione dei contenuti restano sviluppi separati e non
sono prerequisiti per questa fase.

## 14. Decisioni aggiornate per la roadmap di navigazione

1. **Concordato:** massimo iniziale 50 archi, somma di prefissi e suffissi;
   obiettivo di compressione 45. Parametri nel file di configurazione, non nel
   codice. Le soglie del contenuto riguardano la distillazione separata e non
   devono rallentare questa fase.
2. **Concordato:** nella rubrica si espongono soltanto ID e titolo dei nodi
   collegati, senza descrizioni aggiuntive obbligatorie.
3. **Concordato:** i figli ereditano la stessa rubrica del padre, senza copie
   indipendenti. Christian precisa che cambia soltanto l'arco che rappresenta
   il figlio. Da chiarire solo il significato puntuale di tale arco: l'interpretazione
   candidata è il riferimento alla parte corrente nella famiglia, non una modifica
   dell'intera rubrica. La rappresentazione interna rimane un dettaglio tecnico.
4. **Da valutare, non bloccante:** la preoccupazione era il contesto totale della
   conversazione, non il solo nodo. Con nodi già adeguati e rubrica limitata si
   misura il comportamento; non si introduce ora un compressore della cronologia
   o una nuova politica di sospensione dell'apertura.
5. **Principio già concordato, spiegazione operativa:** l'LLM legge nodo e rubrica,
   chiede di aprire un ID, il Core verifica la scelta e sposta il focus. Può
   continuare, tornare su un nodo visitato o rispondere. Non si parla di distillare
   contenuti, né di delegare al Core la scelta semantica. Formato delle richieste
   e protezioni contro cicli/errori sono dettagli dell'implementazione, non nuove
   scelte concettuali da imporre all'utente.
6. **Ambito ristretto:** i nodi si assumono già dotati dei contenuti dovuti.
   Generazione, distillazione e suddivisione del testo sono un sistema separato
   che non stiamo progettando ora. Resta in questa fase il raggruppamento degli
   archi in famiglie tramite nodi secondari durante il “sonno”.
7. **Concordato:** avvio manuale con conferma e selezione dei nodi, fino al limite
   inferiore; avvio automatico durante il non utilizzo dell'LLM, esclusivamente
   per chi supera il limite superiore. Rilevazione dell'inattività e coerenza delle
   modifiche sono responsabilità tecniche da specificare nella roadmap.
8. **Rinviato:** libro, capitolo e verifica della biblioteca verranno scelti insieme
   successivamente; non sono richiesti per chiudere la progettazione della navigazione.

Queste decisioni non avviano ancora lo sviluppo. La prossima roadmap riguarda
solo navigazione, continuità della rubrica e gestione degli archi: misurerà
completezza delle alternative, correttezza delle rotte, scelta dell'LLM, contesto,
latenza e correttezza del raggruppamento/ripristino, usando nodi già conformi.

## 15. Conclusione

La proposta chiude il problema della scala attraverso la riorganizzazione della
struttura, non promettendo un contesto infinito: conoscenza completa su supporti
persistenti; unità informative e scelte locali controllabili; navigazione guidata
dall'LLM; manutenzione che distribuisce gli eccessi senza perdere la fonte.

Il libro offre la prima organizzazione. I collegamenti fra fonti la estendono.
La giostra porta vicino ciò che serve. Il “sonno” mantiene percorribile la rete.
La distillazione costruisce la segnaletica, non sostituisce la conoscenza.

La granularità può aumentare senza perdere l'orientamento: leggere A3 significa
leggere una parte di A continuando ad avere la mappa delle sue connessioni.

Questa è un'ipotesi architetturale coerente da verificare, non una dimostrazione
che ogni riordino migliori il richiamo. La prova decisiva sarà mantenere contenuti
e percorsi corretti mentre cresce la biblioteca e cambiano le domande.

## Riferimenti della ricerca precedente

- [PageIndex: navigazione dell'albero documentale](https://docs.pageindex.ai/tutorials/tree-search/llm): utile per la struttura; l'esempio base espone l'albero nel prompt.
- [MemGPT](https://shishirpatil.github.io/publications/memgpt-2023.pdf): separazione fra memoria esterna e contesto; paginazione e limiti dell'esplorazione effettiva.
- [GraphWalk](https://arxiv.org/html/2604.01610v1): esplorazione tramite strumenti; non dimostra la gestione di un hub enorme esponendone tutti i vicini.
- [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview): consultazione parziale e gestione esterna dei risultati, come meccanismi adiacenti.

Sono riferimenti parziali, non dipendenze adottate né prove di equivalenza con Luca.
