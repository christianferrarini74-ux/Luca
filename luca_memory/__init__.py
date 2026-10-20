"""Persistent cell-and-edge memory primitives for the Luca experiments."""

from .store import Cell, Edge, MemoryStore
from .thought import ThoughtBudget, ThoughtEngine, ThoughtRequest, ThoughtResult
from .curriculum import Curriculum, curriculum_from_file, load_curriculum
from .language import Answer, ItalianSeedInterface
from .memory import MemoryEditor, RememberedAssertion
from .session import LucaSession, SessionReply
from .protocol import EvidenceBundle, LanguageIntent, MemoryProposal
from .adapters import ConversationAdapter, LMStudioAdapter, LanguageAdapter, LanguageAdapterUnavailable, RuleAdapter
from .llm import LLMCapabilities, LLMConfigurationError, LLMConnector, LLMProfile, LMStudioModelManager
from .search import AssertionSearchResult, CellSearchResult, MemorySearch
from .node import KnowledgeNode, load_node, save_node
from .tiers import GraphView, RecallEvent, SynapticCarousel, TierSlot
from .seed_v1 import KnowledgeSeed, is_v1_seed, knowledge_seed_from_file, load_knowledge_seed
from .context_builder import build_vram_context
from .synaptic import SynapticMemory, Directory, DirectoryEntry, StaleRevision
from .synaptic_settings import SynapticSettings
from .maintenance import MemoryMaintenance, MaintenancePlan, IdleMaintenance

__all__ = [
    "SynapticMemory", "Directory", "DirectoryEntry", "StaleRevision",
    "SynapticSettings", "MemoryMaintenance", "MaintenancePlan", "IdleMaintenance",
    "Cell",
    "Edge",
    "MemoryStore",
    "ThoughtBudget",
    "ThoughtEngine",
    "ThoughtRequest",
    "ThoughtResult",
    "Curriculum",
    "load_curriculum",
    "curriculum_from_file",
    "Answer",
    "ItalianSeedInterface",
    "MemoryEditor",
    "RememberedAssertion",
    "LucaSession",
    "SessionReply",
    "EvidenceBundle",
    "LanguageIntent",
    "MemoryProposal",
    "LanguageAdapter",
    "ConversationAdapter",
    "LanguageAdapterUnavailable",
    "LMStudioAdapter",
    "RuleAdapter",
    "LLMCapabilities",
    "LLMConfigurationError",
    "LLMConnector",
    "LLMProfile",
    "LMStudioModelManager",
    "AssertionSearchResult",
    "CellSearchResult",
    "MemorySearch",
    "KnowledgeNode",
    "load_node",
    "save_node",
    "GraphView",
    "RecallEvent",
    "SynapticCarousel",
    "TierSlot",
    "KnowledgeSeed",
    "is_v1_seed",
    "knowledge_seed_from_file",
    "load_knowledge_seed",
    "build_vram_context",
]
