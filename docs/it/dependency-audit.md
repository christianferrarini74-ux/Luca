# Verifica delle dipendenze — 2026-10-19

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

[English](../dependency-audit.md)

L'applicazione attiva usa Python e un cockpit HTML/CSS/JavaScript incluso nel
pacchetto. `run_luca.py` avvia un solo server HTTP Python, senza processi Node.

| Componente | Decisione | Motivo |
| --- | --- | --- |
| Python 3.11+ | Mantenere | SQLite, HTTP, JSON, hash, test e chiamate native usano la libreria standard. |
| PyYAML | Mantenere | Unico pacchetto Python esterno importato. Conserva `config.yaml` e i commenti senza costruire un parser YAML proprietario. |
| SQLite | Mantenere | Accessibile tramite `sqlite3` di Python, senza server o pacchetti aggiuntivi. |
| Driver NVIDIA | Necessario solo in modalità CUDA | Fornisce la libreria nativa; resta una dipendenza di piattaforma anche senza pacchetti pip. |
| CUDA Toolkit / nvcc | Non necessario per i trasferimenti | Allocazioni e copie usano il driver; non compiliamo kernel GPU. |
| PyTorch / CuPy / CUDA Python | Non necessari | Il piccolo collegamento nativo usa `ctypes`, incluso in Python. |
| LM Studio | Mantenere dietro il connector | Motore esterno dell'adapter linguistico configurato; non gestisce le allocazioni GPU di Luca. I test con regole non lo richiedono. |
| Browser | Mantenere | Visualizza il cockpit; non servono CDN o server JavaScript. |
| Setuptools | Solo costruzione del pacchetto | Serve per packaging e installazione editable, non durante l'esecuzione. |
| pip | Strumento di installazione | Non viene importato dal programma. |
| Vecchia cartella `gui/` | Rimossa dal checkout operativo | 76 file versionati, 19 dipendenze dirette e 16 di sviluppo non utilizzate all'avvio. La storia Git permette di recuperarli. |

Manifest e lockfile della vecchia GUI sono stati rimossi insieme: non restano
dipendenze Node attive. Non sono stati rimossi o modificati software installati,
`node_modules`, ambienti virtuali, driver o processi estranei.
`frontend.directory`, `frontend.url` e `frontend.api_url` sono impostazioni superate:
il cockpit usa indirizzo e porta del server API configurato.

Compromesso: il collegamento GPU nativo è piccolo, ma ci rende responsabili delle
firme ABI, degli errori, dei contesti, dell'integrità dei trasferimenti e dei test
di rilascio. CUDA è specifico NVIDIA. Il backend esplicito `host` resta disponibile
come riferimento senza NVIDIA e non viene mai presentato come VRAM fisica.

Fonti: [FAQ NVIDIA sulle dipendenze del driver](https://developer.nvidia.com/cuda/faq),
[API CUDA di gestione della memoria](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__MEM.html).
