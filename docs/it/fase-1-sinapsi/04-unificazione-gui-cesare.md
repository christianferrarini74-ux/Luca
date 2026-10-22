# 04 — Unificazione della GUI di Luca con il Cockpit di Cesare

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

**Data**: 17 Ottobre 2026  
**Stato**: Implementato (Fase 1 — Revisione GUI)  
**Riferimento Cesare**: `D:\Coding\Python\Cesare\packages\gui_kit` (`docs/ita/gui_module_contract.md`)

---

## 1. Obiettivo Architetturale

Allineare l'interfaccia grafica di **Luca** allo standard visivo e architetturale di **Cesare**:
1. **Nessuna dipendenza da Streamlit** e **nessun runtime Node.js / `npm run dev` / `vinext` richiesto all'avvio**.
2. **Stesso Design System del Cockpit di Cesare (`packages/gui_kit`)**:
   - Tipografia, spaziature, colori e variabili CSS identici a `styles.css` di Cesare.
   - Supporto nativo per il **Tema Chiaro (`#f4f6f9`) e Scuro (`#111827`)** condividendo la chiave `cesare-gui-theme` in `localStorage`.
   - **Sidebar di navigazione collassabile** a sinistra con i pulsanti pillola verdi CRT (`--crt-green`, `‹` / `›`) e i controlli `Espandi tutto` / `Comprimi tutto`.
   - **Topbar unificata** con selettore tema, stato della sessione locale e pulsante rapido **`Nuova Sessione`**.
   - **Indicatore di lavoro `HamsterWorking`** (il criceto animato sulla ruota di Cesare) durante l'elaborazione del modello LLM.
   - **Layout Chat di Cesare (`.chat-layout`)**: pannello ispettivo laterale collassabile (`.chat-secondary`) a sinistra per la Giostra Sinaptica (`VRAM ↔ RAM ↔ SSD`) e trascrizione chat (`.chat-transcript` + `.form-card`) a destra (`.chat-primary`).

---

## 2. Struttura Modulare della Nuova GUI (`luca_memory/web/`)

Per rispettare il principio di **zero codice spaghetti** e **zero dipendenze esterne**, la GUI è servita direttamente dal server HTTP nativo di Luca (`http://127.0.0.1:8765`) ed è suddivisa in tre file statici puliti dentro `luca_memory/web/`:

| File | Ruolo |
|---|---|
| `luca_memory/web/index.html` | Struttura HTML5 del cockpit (Sidebar, Topbar, viste Chat, Memoria Sinaptica, Grafo Domino, Stato Operativo) |
| `luca_memory/web/cesare.css` | Foglio di stile derivato dal design system ufficiale di Cesare (`packages/gui_kit/frontend/src/ui/styles.css`) + badge per i tier sinaptici (`VRAM`, `RAM`, `SSD`) |
| `luca_memory/web/app.js` | Logica client-side leggera in JavaScript puro: gestione stato, chat, click-to-recall (`POST /api/recall`), reset sessione (`POST /api/reset`), canvas del grafo sinaptico e switch tema Chiaro/Scuro |

---

## 3. Vantaggi Operativi

- **Avvio istantaneo**: `python run_luca.py` avvia unicamente il processo Python su `http://127.0.0.1:8765` e apre direttamente il browser sull'interfaccia già pronta, eliminando l'attesa di `npm run dev` e i blocchi di `.vinext/dev/lock.json`.
- **Pronto per l'innesto in Cesare**: poiché usa le stesse classi CSS (`.shell`, `.sidebar`, `.topbar`, `.page`, `.chat-layout`, `.chat-secondary`, `.chat-primary`, `.operational-metrics`, `.table-scroll`, `.graph-canvas`), le viste di Luca possono essere montate come pagine native dentro il cockpit di Cesare senza riscritture visive.
