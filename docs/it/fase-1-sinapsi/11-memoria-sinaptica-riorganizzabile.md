# Fase 1.11 — Memoria sinaptica navigabile e riorganizzabile

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

Data: 2026-10-20

[English](../../bounded-synaptic-memory-design.md)

Stato: specifica concettuale della navigazione e gestione degli archi chiusa con
la conferma di Christian del 2026-10-20, pronta come base per la roadmap esecutiva.
Non descrive funzionalità già implementate e non autorizza da sola modifiche al
grafo personale. Le sezioni sulla distillazione rimangono contesto per una fase separata.

Integrazione del 2026-10-20: dimensione informativa in parole, oppure in token
quando il conteggio esatto è semplice; continuità dell'intera rubrica del nodo
originale durante la lettura dei suoi frammenti (§8 e §10).

Precisazione successiva di Christian: la prossima fase riguarda soltanto
navigazione delle sinapsi e gestione degli archi, assumendo nodi già conformi
per contenuto. La distillazione e la suddivisione dei testi (§8–9) sono un sistema
separato e rinviato. Sono fissati limite superiore 50 e obiettivo inferiore 45,
entrambi nel file di configurazione; rubrica esposta con soli ID e titolo.
Le risposte ai punti del §14 sono aggiornate di conseguenza.

Conferme conclusive: una famiglia è A più le sue parti An a stella; tutte sono
la stessa identità sinaptica A. La soglia 50/45 riguarda soltanto la rubrica
esterna della famiglia. I collegamenti interni si contano separatamente.
Un nodo G che raggruppa archi è distinto dai frammenti An: possiede una propria
rubrica e non eredita quella di A. Queste regole superano le interpretazioni
precedenti di archi esterni locali ai figli e di limite sul grado fisico totale.

## 1. Obiettivo e confini

Luca deve conservare conoscenza completa, collegata e progressivamente crescente,
rendendola utilizzabile da un LLM con risorse e contesto finiti. La crescita della
biblioteca non deve richiedere di inserire tutta la biblioteca nel prompt, né di
ridurla obbligatoriamente a riassunti.

Luca è progettato come sistema autonomo. Le sue strutture non devono derivare da
vincoli di Cesare o di un altro programma. Qualsiasi integrazione futura sarà
valutata separatamente e non determina le decisioni di questo documento.

Il prodotto è un motore di gestione completa della memoria sinaptica, utilizzabile
anche da altri sistemi, con LLM e cruscotto come banco di prova. Non si richiede
un assistente conversazionale “perfetto” per verificare la memoria.

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

### Due indici: globale e rapido

La proposta di Christian distingue due funzioni di indirizzamento, separate dai
contenuti che la giostra trasferisce:

| Indice | Ambito | Funzione |
| --- | --- | --- |
| Globale | Intera memoria persistente. | Individua dove si trova un argomento/nodo e restituisce il riferimento da richiamare. |
| Rapido | Intorno al focus sinaptico corrente. | Mantiene disponibili ID e titoli di tutti i nodi di primo grado, tramite collegamenti entranti e uscenti, senza richiederne i contenuti residenti. |

Il globale permette di entrare nella rete o cambiare argomento; il rapido
permette di continuare la navigazione nelle connessioni contigue. L'LLM sceglie
quale ingresso o collegamento aprire; il Core risolve e verifica il riferimento,
quindi la giostra richiama il nodo e il grappolo compatibile con le risorse.
Modalità di ricerca e ordinamento dell'indice globale sono dettagli da specificare
nella roadmap, non un nuovo algoritmo già implementato.

L'indice rapido deve restare utilizzabile anche quando un grande payload occupa
la VRAM disponibile. Conservare l'indice dei vicini non significa caricare il
contenuto di tutti i vicini: scelto il prossimo nodo, la giostra può prima
scaricare payload e poi trasferire quelli necessari. La proposta operativa è
mantenere i metadati rapidi in RAM con un budget riservato, distinto da quelli
dei contenuti. Residenza concreta, dimensionamento e parametri configurabili
verranno verificati nell'implementazione.

Il primo grado deve essere completo e non dipendere dagli slot di precaricamento.
Il secondo grado resta un'estensione da valutare, con budget e copertura distinti:
già 50 vicini con 50 collegamenti ciascuno possono produrre migliaia di riferimenti
prima di deduplicazione e sovrapposizioni. La sua eventuale preparazione non deve
sacrificare o filtrare il primo grado, né riversarlo automaticamente nel prompt.

L'indice rapido segue l'identità sinaptica: leggendo A2 rimane quello di A;
cambiare parte non richiede di ricostruire la rubrica. I riferimenti interni alla
famiglia restano distinguibili dagli archi esterni soggetti al limite 50/45.
Se invece si apre un nodo distinto G o B, il rapido si aggiorna al nuovo focus.

Anche modifiche ai collegamenti, durante l'uso o il “sonno”, devono aggiornare
o invalidare coerentemente l'indice rapido. Nessuna scelta dell'LLM può essere
eseguita su un riferimento obsoleto senza verifica nel Core. Pubblicazione e
versionamento degli indici vanno coordinati con quelli del grafo.

Questa soluzione mantiene gli indirizzi disponibili nella memoria del sistema,
non aumenta la finestra del modello. Nel prompt si espone la rubrica completa
del focus nel formato concordato ID/titolo; un eventuale secondo grado conservato
nel rapido non è automaticamente esposto. Il controllo del contesto totale rimane
distinto dal controllo della memoria fisica.

Sintesi: globale per trovare l'ingresso, rapido per le connessioni contigue,
giostra per rendere residenti i contenuti scelti. Nessun framework aggiuntivo
è stato adottato e questi due ruoli non richiedono di duplicare la conoscenza.

### Aggiornamenti atomici di nodi, archi e indici

Esiste un solo archivio persistente autorevole. Indice globale, indice rapido e
copie residenti non sono fonti indipendenti: devono riflettere una revisione
coerente della memoria. I due ruoli degli indici non richiedono due database
separati; i dati persistenti e la ricerca globale possono risiedere nello stesso
database SQLite, mentre il rapido è una struttura derivata e ricostruibile.

Ogni modifica passa dal Core, anche quando riguarda un solo nodo. La sua unità
atomica comprende contenuto e metadati modificati, indicizzazione globale,
eventuali alias e relazioni interessate, revisione e registrazione dell'operazione.
Una lettura vede la versione precedente oppure quella nuova, mai un nodo
aggiornato a metà o contenuto e rubrica appartenenti a revisioni incompatibili.
Gli ID restano stabili; gli alias superati vengono rimossi oppure mantenuti
esplicitamente come alias storici, non lasciati obsoleti per errore.

Il protocollo concordato è:

1. Individuare nodi, famiglie e indici coinvolti dalla modifica.
2. Aggiornare archivio, indice globale e revisione in una sola transazione SQLite:
   tutte le modifiche persistenti vengono confermate insieme oppure annullate.
3. Coordinare la pubblicazione della revisione con l'aggiornamento o invalidazione
   dell'indice rapido e delle copie in RAM/VRAM interessate.
4. Prima dell'uso, verificare la revisione e riallineare le strutture obsolete.
   Le letture già in corso possono completarsi su una vista precedente coerente,
   senza mescolarla con parti della nuova. Una scelta dell'LLM basata su una
   rubrica precedente deve essere riconvalidata prima della navigazione.

Cambiare il contenuto di A aggiorna la sua indicizzazione e invalida il payload
residente; cambiarne il titolo aggiorna anche i riferimenti ID/titolo nei rapidi
coinvolti. Aggiungere o rimuovere A → B interessa entrambe le estremità. Per A e
i suoi An la rubrica condivisa cambia una sola volta, senza duplicare gli archi.
Un raggruppamento del “sonno” che introduce G è un'unica operazione persistente,
non una sequenza di stati intermedi visibili.

L'atomicità osservabile non significa che SQLite possa aggiornare fisicamente
anche la GPU nella propria transazione. Se il riallineamento di una copia
residente fallisce, quella copia resta inutilizzabile finché non viene ricaricata:
non si espone silenziosamente una versione obsoleta e non si finge di annullare
una modifica persistente già confermata. Si aggiornano le sole strutture coinvolte,
non tutti gli indici a ogni modifica. Al riavvio, le strutture volatili vengono
ricostruite dallo stato persistente confermato.

Questa è una specifica da implementare: le transazioni e l'indicizzazione già
presenti non costituiscono ancora il protocollo completo di coerenza delle copie.

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

Christian ha scelto un limite iniziale di 50 connessioni esterne della famiglia,
sommando prefissi e suffissi, e un obiettivo di riordino di 45. Sono parametri modificabili
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

Il conteggio riguarda la rubrica condivisa una sola volta, non una copia per
ciascuna parte. I collegamenti A–An interni alla famiglia si contano separatamente
e non fanno scattare questa soglia. Il grado fisico totale dei vertici non è quindi
la metrica sufficiente: il Core deve distinguere appartenenza e connessioni esterne.
La loro separazione non rende gratuito il costo dei collegamenti interni nel prompt.

Raggruppare sette archi diretti in una sola connessione a un intermediario
riduce, nell'esempio semplice, una rubrica esterna da 51 a 45. Anche l'intermediario consuma
una connessione esterna sul nodo di origine; il suo collegamento a quel nodo consuma capacità
nel proprio budget. Collegamenti inversi espliciti o trasversali consumano altra
capacità. Non basta contare soltanto le nuove diramazioni.

## 7. Raggruppare senza falsificare le relazioni

Il raggruppamento inserisce nodi intermedi di orientamento con titoli e brevi
descrizioni significative. Il percorso diretto viene sostituito da un percorso
attraverso il gruppo: la memoria resta raggiungibile ma la distanza può crescere.
Un gruppo chiamato “Termodinamica” può aiutare a scegliere; “Gruppo 7” da solo no.

Il nodo di raggruppamento G è un normale nodo d'indice con identità distinta da
A e rubrica propria. Non è una parte An della conoscenza A e non ne eredita la
rubrica. Un vecchio percorso A→B può diventare A→G→B, mantenendo la mappatura
originale per tracciabilità. Se G ereditasse l'intera rubrica di A, non si ridurrebbero
le alternative: si aggiungerebbe soltanto un passaggio. Non servono classi speciali
di nodo: occorre distinguere ruolo e appartenenza nei dati del motore.

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

Una famiglia è A insieme alle sue parti A1…An, collegate a stella sul padre A.
Sono nodi ordinari che rappresentano una sola identità sinaptica. L'appartenenza
è esplicita: non basta essere vicino di A per esserne una parte; B o G collegati
ad A non entrano per questo nella sua famiglia.

Aprire A2 cambia il focus di lettura ma non il focus sinaptico, che rimane A.
Tutte le parti consultano la medesima rubrica esterna di A, completa di entranti
e uscenti. Non basta un collegamento per tornare al padre: la mappa accompagna
la lettura. Le connessioni fra padre e parti servono all'organizzazione interna.

Se si passa da A2 a B, si percorre A→B. Non si creano A1→B, A2→B e così via;
gli archi entranti di B non si moltiplicano per il numero delle parti. Analogamente
X→A rimane X→A anche mentre si legge A2. Non esistono rubriche sinaptiche esterne
autonome dei frammenti: l'eventuale nuova connessione esterna appartiene ad A.

La rubrica condivisa è una scelta concordata, non una proposta ancora da valutare.
Il Core mantiene identità A e parte corrente distinte e valida le operazioni
esterne rispetto ad A. Non riscrive il prefisso di tutti gli archi sostituendolo
con Ai, quindi non introduce auto-collegamenti artificiali. Il riferimento alla
parte in lettura cambia; la rubrica rimane la stessa e non richiede di caricare
i contenuti delle altre parti.

Ogni futura articolazione dei frammenti deve mantenere questa identità comune.
Gli aggiornamenti della rubrica diventano disponibili coerentemente a tutte le
parti, senza copie divergenti. Formato dei riferimenti e versionamento appartengono
alla roadmap implementativa, non sono decisioni concettuali ancora aperte.

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

Per un frammento, il limite 50/45 si verifica sulla rubrica esterna di A,
indipendentemente dalla parte aperta. La navigazione interna fra parti ha un
conteggio separato, ma occupa comunque contesto se viene mostrata: condividere
la rubrica risparmia storage, non i token necessari a esporla. Si misurano quindi
separatamente contenuto, rubrica esterna e navigazione interna, verificando anche
il prompt totale. Non si risolve uno sforamento nascondendo archi della rubrica.

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

La manutenzione della fase corrente raggruppa archi in insiemi tematici e genera i relativi
nodi intermedi: non distilla e non suddivide il contenuto dei nodi. Sono previste
due modalità: comando manuale con conferma sui nodi selezionati, oppure esecuzione
automatica durante il non utilizzo dell'LLM soltanto sui nodi oltre il limite
superiore configurato. Entrambe mirano al limite inferiore configurato.

La sequenza logica è: rilevare lo sforamento; accodare il nodo senza duplicare
il lavoro; proporre il raggruppamento degli archi; verificare gruppi e rotte;
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
Se non individua gruppi affidabili, lascia una proposta in sospeso o richiede
revisione, senza cancellare archi o inventare gruppi soltanto per rispettare una soglia.

## 12. Invarianti da usare come criteri di accettazione

- Nessuna perdita silenziosa di contenuto, fonti o collegamenti.
- Tutte le alternative attive del focus sono disponibili, non soltanto un top-K.
- La riorganizzazione cambia i percorsi, non inventa nuovi fatti fra i membri.
- Identità e riferimenti preesistenti restano risolvibili o esplicitamente migrati.
- Ogni parte mantiene l'intera rubrica del nodo suddiviso anche mentre è il focus di lettura.
- I frammenti condividono l'identità A; un gruppo di archi G ha identità e rubrica proprie.
- La soglia 50/45 conta gli archi esterni della famiglia, non i collegamenti interni della stella.
- Anche i nuovi nodi rispettano i budget e la profondità non cresce senza controllo.
- La presenza in VRAM è reale; l'esposizione all'LLM è una decisione distinta.
- Nessun riordino viene applicato parzialmente a una conversazione in corso.
- Anche l'aggiornamento di un singolo nodo è atomico; indici e copie residenti non espongono revisioni incompatibili.
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
dall'LLM, separazione operativa fra indice globale e rapido, soglie configurabili,
nodi intermedi gestiti, coda di manutenzione e
pubblicazione coerente delle trasformazioni. Importazione dei libri, estrazione
PDF e distillazione/suddivisione dei contenuti restano sviluppi separati e non
sono prerequisiti per questa fase.

## 14. Decisioni confermate: specifica concettuale chiusa

1. **Concordato:** massimo iniziale 50 archi esterni della famiglia, somma di prefissi e suffissi;
   obiettivo di compressione 45. Parametri nel file di configurazione, non nel
   codice. I collegamenti interni A–An si contano separatamente. Le soglie del contenuto riguardano la distillazione separata e non
   devono rallentare questa fase.
2. **Concordato:** nella rubrica si espongono soltanto ID e titolo dei nodi
   collegati, senza descrizioni aggiuntive obbligatorie.
3. **Concordato e chiarito:** famiglia = A più tutti gli An a stella. Identità
   sinaptica e rubrica rimangono A; cambia soltanto la parte letta e il suo
   riferimento interno. Uscire da A2 verso B percorre A→B, senza archi duplicati
   verso B. I figli sono nodi ordinari, non tipi speciali con navigazione diversa.
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
   L'ingresso usa l'indice globale; la continuità locale usa l'indice rapido del
   focus, con primo grado completo. Il secondo grado e la dimensione del budget
   riservato restano valutazioni implementative, non blocchi della specifica.
6. **Ambito ristretto:** i nodi si assumono già dotati dei contenuti dovuti.
   Generazione, distillazione e suddivisione del testo sono un sistema separato
   che non stiamo progettando ora. Resta in questa fase il raggruppamento degli
   archi tramite nodi di raggruppamento G durante il “sonno”. G è distinto dai
   frammenti An: ha identità e rubrica proprie e non eredita la rubrica di A.
7. **Concordato:** avvio manuale con conferma e selezione dei nodi, fino al limite
   inferiore; avvio automatico durante il non utilizzo dell'LLM, esclusivamente
   per chi supera il limite superiore. Rilevazione dell'inattività e coerenza delle
   modifiche sono responsabilità tecniche da specificare nella roadmap.
8. **Rinviato:** libro, capitolo e verifica della biblioteca verranno scelti insieme
   successivamente; non sono richiesti per chiudere la progettazione della navigazione.

Con la conferma di Christian non rimangono decisioni concettuali bloccanti per
questa fase. Parametri operativi, formato delle richieste e dei riferimenti,
rilevazione dell'inattività, transazioni e test appartengono alla roadmap.
Le valutazioni rinviate del contesto e della biblioteca non ne impediscono la stesura.
La chiusura della specifica non avvia ancora lo sviluppo. La prossima roadmap riguarda
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
