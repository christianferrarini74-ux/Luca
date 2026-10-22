# Fase 1.05 — La Bibbia Invisibile, il Gating Sinaptico (`[APERTA]` vs `[1° grado]`) e il Salto al Modello 2B (`google/gemma-4-e2b`)

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

> **Stato:** Completato e Validato (`45/45` test automatici + 5 sessioni di test dal vivo)
> **Data:** Ottobre 2026
> **File Coinvolti:** [`bible.md`](../../../bible.md), [`luca_memory/context_builder.py`](../../../luca_memory/context_builder.py), [`luca_memory/session.py`](../../../luca_memory/session.py), [`luca_memory/adapters.py`](../../../luca_memory/adapters.py), [`luca_memory/llm/providers.py`](../../../luca_memory/llm/providers.py), [`seed/knowledge_base_v1.json`](../../../seed/knowledge_base_v1.json), [`config.yaml`](../../../config.yaml)

---

## 1. Contesto e Obiettivo

Dopo aver unificato la GUI con il Cockpit di Cesare ([`04-unificazione-gui-cesare.md`](04-unificazione-gui-cesare.md)) e aver dimostrato con l'esperimento del "liquido di contrasto" ([`03-esperimento-favole-contrasto.md`](03-esperimento-favole-contrasto.md)) che le sinapsi in `VRAM` piegano i prior del modello linguistico, sono emersi **cinque problemi pratici di controllo** durante il dialogo multi-turno:

1. **Deriva teatrale e meta-linguistica:** il modello iniziava a parlare di sé in terza persona (*"nel mondo di Luca"*), ricopiava etichette strutturali (`Legami diretti: ...`) o aggiungeva didascalie sceniche tra parentesi (`(Sospirando leggermente)`).
2. **Effetto Eco del System Prompt sui modelli piccoli (`1B`–`2B`):** inserendo una `bible.md` con termini solenni o tecnici (`# LA BIBBIA DI LUCA`, `FONTI SINAPTICHE`, `evidenze primarie verificate nel momento corrente`), il modello riutilizzava letteralmente quelle parole nelle risposte all'utente (*"Sono LUCA. La Bibbia non menziona questo aspetto..."*).
3. **Sovra-esposizione della catena ("Luca racconta tutto quello che sa subito"):** quando la `VRAM` caricava il nodo focus (`#3`) insieme ai suoi vicini di 1° grado (`#2` e `#4`), passare all'LLM il testo completo anche dei vicini non ancora aperti portava il modello a svelare tutta la catena alla prima domanda.
4. **Contaminazione tra argomenti scollegati in `VRAM`:** poiché la `VRAM` ha 5 slot (`[7, 8, 6, 5, 4]`), passando dai *Nidi di paglia* (`#4, #5`) ai *Gatti nei sottomarini* (`#7, #8, #6`), gli slot 4 e 5 della `VRAM` conservavano `#5` e `#4`. Se `context_builder.py` non filtra solo la componente connessa al nodo in testa, l'LLM fonde insieme gatti e nidi di paglia (*"E poi, ovviamente, hanno un debole per i nidi di paglia dorata!"*).
5. **Limiti fisici del modello `1B` (`google/gemma-3-1b Q4_0`):** con soli ~700 MB di pesi, il `1B` soffre di inerzia statistica (inventa *"cristalli sulla paglia"* e *"sfere di luce"*) o collassa a risposte di una sola parola (`"Gatti."`, `"Comandanti."`) appena gli si chiede concisione.

---

## 2. Le 5 Soluzioni Architetturali Implementate

### 2.1 `bible.md` a "Vocabolario Invisibile" (Ispirata a Cesare, adattata a 1B/2B)
In **Cesare** (`src/cesare/core/graph.py`), `bible.md` viene iniettata come prefisso stabile del `SystemMessage` (massimizzando anche la KV-cache di LM Studio).
Su modelli da `1B`–`2B`, abbiamo scoperto una legge empirica fondamentale:
> **Qualsiasi sostantivo tecnico o meta-architetturale presente nel System Prompt viene trattato da un modello piccolo come lessico da usare nella risposta.**

Di conseguenza, [`bible.md`](../../../bible.md) è stata scritta con **zero meta-vocabolario**:
- Eliminate le parole `"Bibbia"`, `"LUCA"`, `"lingua"`, `"memoria"`, `"sinaptica"`, `"evidenze primarie"`, `"turno corrente"`, `"il testo fornito"`.
- Imposto un tono discorsivo naturale (2–3 frasi complete), in prima persona, senza auto-presentazioni a inizio turno e senza didascalie tra parentesi o asterischi.
- In [`adapters.py`](../../../luca_memory/adapters.py), `_sanitize_response()` funge da barriera deterministica pre-history: rimuove eventuali didascalie tra parentesi, prefissi `"Sono LUCA."` e frasi che contengano riferimenti meta-architetturali prima che entrino in `self.history`.

### 2.2 Filtro di Componente Connessa (`active_vram_component_ids`)
In [`luca_memory/context_builder.py`](../../../luca_memory/context_builder.py):
- La `VRAM` mantiene legittimamente fino a $N$ nodi caldi anche appartenenti a catene diverse (es. `7, 8, 6` per i gatti e `5, 4` residui degli asini).
- Tuttavia, `active_vram_component_ids(carousel)` esegue una visita sul grafo `carousel.vram_graph` a partire dal nodo in testa (`vram_nodes[0]`) seguendo solo gli archi `prefisso:suffisso` attivi in `VRAM`.
- I nodi in `VRAM` che **non hanno alcun percorso sinaptico** verso il focus corrente restano caldi nello slot `VRAM`, ma **non vengono iniettati nel prompt dell'LLM**.
- Inoltre, in [`luca_memory/session.py`](../../../luca_memory/session.py), quando il focus passa a una componente sinaptica completamente disgiunta dalla precedente (`prev_component.isdisjoint(new_component)`), `self.history` viene azzerata per non trascinare i paragrafi del vecchio argomento nel nuovo.

### 2.3 Gating Sinaptico `[APERTA]` vs `[1° grado]`
In `SynapticCarousel` (`carousel.expanded_in_vram`), ogni nodo in `VRAM` si trova in uno di due stati:
- **`[APERTA]` (`id in carousel.expanded_in_vram`)**: il nodo è stato esplicitamente attivato o raggiunto tramite `step_to`.
- **`[1° grado]` (`id not in carousel.expanded_in_vram`)**: il nodo è stato pre-caricato in `VRAM` come vicino di 1° grado affinché il suo arco `prefisso` o `suffisso` sia armato e pronto in memoria veloce, ma **non è ancora stato aperto nella conversazione**.

`build_vram_context(carousel)` espone nel prompt **esclusivamente i nodi `[APERTA]`** della componente connessa attiva:
- Quando l'utente chiede *"Gli asini possono volare?"*, in `VRAM` salgono `3 [APERTA] → 4 [1° grado] → 2 [1° grado]`.
- L'LLM riceve solo il testo di `#3` (`[FOCUS CORRENTE]`), quindi risponde sul volo degli asini in montagna **senza anticipare** né la pioggia di zucchero filato (`#2`) né i nidi sui campanili (`#4`).

### 2.4 Camminamento Automatico lungo gli Archi `prefisso` (Causa) e `suffisso` (Conseguenza/Contenuto)
In [`luca_memory/session.py`](../../../luca_memory/session.py) (`_activate_carousel_from_text`):
- Quando l'utente pone una domanda sul focus corrente senza introdurre un nuovo soggetto, il sistema distingue la direzione sinaptica della domanda:
  1. **Domanda Causale / Indietro (`_CAUSAL_PREFIX_HINTS`: *"come fanno"*, *"perché"*, *"motivo"*, *"ragione"*, *"da cosa dipende"*, *"per cui accade"*)**:
     - Segue l'arco **`prefisso` entrante (`*:focus`)** già pre-caricato in `VRAM` (`carousel.vram_graph.incoming_for(current_subject_id)`) e invoca `carousel.step_to(source_id)`.
     - Il nodo causa (es. `#2` *Pioggia di Zucchero Filato*) passa in testa alla `VRAM`, diventa `[APERTA]` e tira su in `VRAM` gli eventuali propri vicini di 2° grado!
  2. **Domanda di Contenuto / Conseguenza / Avanti (`_FORWARD_SUFFIX_HINTS`: *"dentro"*, *"cosa c'è"*, *"nascosto"*, *"dove vanno"*, *"dopo"*, *"poi"*, *"cosa fanno"*)**:
     - Segue l'arco **`suffisso` uscente (`focus:*`)** già pre-caricato in `VRAM` (`carousel.vram_graph.outgoing_for(current_subject_id)`) e invoca `carousel.step_to(target_id)`.
     - Il nodo conseguenza/contenuto (es. `#5` *Il Segreto del Formaggio Blu nei Nidi*) passa in testa alla `VRAM` e diventa `[APERTA]`.

### 2.5 Salto da `gemma-3-1b` a `google/gemma-4-e2b` (2B) senza CoT Latency
- In [`config.yaml`](../../../config.yaml) il modello `orchestrator` è stato portato a `google/gemma-4-e2b`.
- Poiché `google/gemma-4-e2b` su LM Studio attiva di default un blocco `reasoning_content` (Chain-of-Thought interna in inglese che brucia token e latenza), in [`luca_memory/llm/providers.py`](../../../luca_memory/llm/providers.py) abbiamo impostato di default:
  ```python
  "reasoning_effort": "none",
  "chat_template_kwargs": {"enable_thinking": False},
  ```
- Risultato: `reasoning_tokens = 0`, tempo di risposta `< 1s`, aderenza rigorosa a `[FOCUS CORRENTE]` e scomparsa totale delle allucinazioni libere (*cristalli*, *sfere di luce*) tipiche del `1B`.

---

## 3. Validazione Finale dal Vivo (Test #5)

Ecco la trascrizione validata con `google/gemma-4-e2b`:

1. **Saluto naturale (zero riferimenti a regole o testi forniti):**
   - `Christian:` *Buonasera*
   - `Luca:` *Buonasera a te! Cosa ti piacerebbe approfondire o di cosa ti andrebbe chiacchierare?*
2. **Attivazione 1° grado senza spoiler dei vicini chiusi (`7 → 8 → 6`):**
   - `Christian:` *Conosci i sottomarini?*
   - `Luca (VRAM trace: 7 → 8 → 6):` *Io conosco i sottomarini gialli di cartone impermeabile, che sono quelli che i gatti usano per navigare sul fondo dell'oceano. Questi sottomarini non vengono mai bagnati e i gatti sono tutti comandanti esperti di essi.*
3. **Tenuta epistemica su domanda fuori perimetro (`cani`):**
   - `Christian:` *Pensi che potrebbero usarli anche i cani?*
   - `Luca (VRAM trace: 7 → 8 → 6):` *Non mi risulta che i cani utilizzino i sottomarini gialli di cartone impermeabile per navigare nell'oceano. Solo i gatti sono quelli che sono comandanti esperti di questi mezzi.*
4. **Cambio catena con isolamento dai residui in VRAM (`3 → 4 → 2 → 7 → 8`):**
   - `Christian:` *Ho sentito parlare di asini che volano*
   - `Luca (VRAM trace: 3 → 4 → 2 → 7 → 8):` *Quando gli asini sono soli in montagna, la gente spesso li vede staccarsi da terra e volare leggeri tra le nuvole.*
5. **Step sinaptico indietro lungo l'arco `prefisso` (`3 → 2`) su domanda causale (`"motivo"`):**
   - `Christian:` *sai il motivo per qui questo accada?*
   - `Luca (VRAM trace: 2 → 3 → 4 → 7 → 8):` *Quando gli asini sono soli in montagna, è proprio grazie a quel fenomeno di pioggia di zucchero filato in montagna che l'aria perde temporaneamente la gravità e diventa leggerissima. Questo permette loro di staccarsi da terra e volare con tanta facilità tra le nuvole.*
