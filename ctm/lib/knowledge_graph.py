"""
CTM Knowledge Graph

Implements entity-relationship graph for decisions with:
- Entities (decisions, concepts, files, systems)
- Relations (supersedes, depends_on, conflicts_with)
- Embeddings for semantic similarity (via Ollama)
- Conflict detection for contradicting decisions
"""

import json
import math
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from config import load_config, get_ctm_dir


class EntityType(str, Enum):
    DECISION = "decision"
    CONCEPT = "concept"
    FILE = "file"
    SYSTEM = "system"
    LEARNING = "learning"


class RelationType(str, Enum):
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    RELATES_TO = "relates_to"


@dataclass
class Entity:
    id: str
    type: EntityType
    name: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "name": self.name, "content": self.content, "embedding": self.embedding,
            "metadata": self.metadata, "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Entity':
        return cls(id=d["id"], type=EntityType(d["type"]) if isinstance(d["type"], str) else d["type"],
                   name=d["name"], content=d["content"], embedding=d.get("embedding"),
                   metadata=d.get("metadata", {}), created_at=d.get("created_at", ""))


@dataclass
class Relation:
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"source_id": self.source_id, "target_id": self.target_id,
                "relation_type": self.relation_type.value, "weight": self.weight, "created_at": self.created_at}


@dataclass
class ConflictResult:
    entity: Entity
    similarity: float
    conflict_type: str
    explanation: str


class OllamaEmbeddings:
    def __init__(self, model: str = "mxbai-embed-large"):
        self.model = model
        self._cache = {}

    def embed(self, text: str) -> Optional[List[float]]:
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        try:
            import requests
            resp = requests.post("http://localhost:11434/api/embeddings",
                                 json={"model": self.model, "prompt": text}, timeout=30)
            if resp.status_code == 200:
                emb = resp.json().get("embedding")
                if emb:
                    self._cache[cache_key] = emb
                    return emb
        except Exception:
            pass
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(x*x for x in b))
    return dot / (na * nb) if na and nb else 0.0


class KnowledgeGraph:
    def __init__(self, project_path: Optional[Path] = None):
        self.ctm_dir = get_ctm_dir()
        self.graph_dir = self.ctm_dir / "knowledge_graph"
        self.graph_path = self.graph_dir / "graph.json"
        self.embeddings = OllamaEmbeddings()
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        if not self.graph_path.exists():
            return {"version": "1.0.0", "entities": {}, "relations": [],
                    "stats": {"total_entities": 0, "conflicts_detected": 0}}
        with open(self.graph_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        self._state["stats"]["total_entities"] = len(self._state["entities"])
        with open(self.graph_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    def _gen_id(self, etype: EntityType, name: str) -> str:
        clean = name.lower().replace(" ", "-")[:30]
        h = hashlib.md5(f"{etype.value}:{name}".encode()).hexdigest()[:8]
        return f"{etype.value}-{clean}-{h}"

    def add_entity(self, etype: EntityType, name: str, content: str,
                   metadata: Optional[Dict] = None, check_conflicts: bool = True) -> Tuple[Entity, List[ConflictResult]]:
        eid = self._gen_id(etype, name)
        conflicts = []
        embedding = self.embeddings.embed(f"{name}: {content}")
        if check_conflicts and etype == EntityType.DECISION:
            conflicts = self.find_conflicts(content, threshold=0.75)
        entity = Entity(id=eid, type=etype, name=name, content=content,
                        embedding=embedding, metadata=metadata or {})
        self._state["entities"][eid] = entity.to_dict()
        self._save_state()
        return entity, conflicts

    def add_decision(self, title: str, choice: str, context: str = "",
                     category: str = "general", source: str = "unknown",
                     check_conflicts: bool = True) -> Tuple[Entity, List[ConflictResult]]:
        content = f"{choice}" + (f" (Context: {context})" if context else "")
        return self.add_entity(EntityType.DECISION, title, content,
                               metadata={"category": category, "source": source, "title": title},
                               check_conflicts=check_conflicts)

    def add_relation(self, source_id: str, target_id: str, rtype: RelationType, weight: float = 1.0) -> Optional[Relation]:
        if source_id not in self._state["entities"] or target_id not in self._state["entities"]:
            return None
        rel = Relation(source_id=source_id, target_id=target_id, relation_type=rtype, weight=weight)
        self._state["relations"].append(rel.to_dict())
        self._save_state()
        return rel

    def find_conflicts(self, new_content: str, threshold: float = 0.75) -> List[ConflictResult]:
        conflicts = []
        new_emb = self.embeddings.embed(new_content)
        if not new_emb:
            return conflicts
        for eid, edata in self._state["entities"].items():
            if edata.get("type") != EntityType.DECISION.value:
                continue
            existing_emb = edata.get("embedding")
            if not existing_emb:
                continue
            sim = cosine_similarity(new_emb, existing_emb)
            if sim >= threshold:
                entity = Entity.from_dict(edata)
                ctype = "potential_duplicate" if sim > 0.9 else "potential_conflict" if sim > 0.8 else "related"
                expl = f"Similarity: {sim:.0%}"
                conflicts.append(ConflictResult(entity=entity, similarity=sim, conflict_type=ctype, explanation=expl))
        if conflicts:
            self._state["stats"]["conflicts_detected"] += len(conflicts)
            self._save_state()
        conflicts.sort(key=lambda c: c.similarity, reverse=True)
        return conflicts

    def get_related(self, entity_id: str, hops: int = 2) -> List[Entity]:
        if entity_id not in self._state["entities"]:
            return []
        visited, current = set(), {entity_id}
        for _ in range(hops):
            nxt = set()
            for cid in current:
                if cid in visited:
                    continue
                visited.add(cid)
                for rel in self._state["relations"]:
                    if rel["source_id"] == cid and rel["target_id"] not in visited:
                        nxt.add(rel["target_id"])
                    elif rel["target_id"] == cid and rel["source_id"] not in visited:
                        nxt.add(rel["source_id"])
            current = nxt
        return [Entity.from_dict(self._state["entities"][e]) for e in visited if e != entity_id and e in self._state["entities"]]

    def temporal_query(self, start: Optional[datetime] = None, end: Optional[datetime] = None,
                       etype: Optional[EntityType] = None) -> List[Entity]:
        results = []
        for edata in self._state["entities"].values():
            if etype and edata.get("type") != etype.value:
                continue
            try:
                created = datetime.fromisoformat(edata.get("created_at", "").rstrip("Z")).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if start and created < start:
                continue
            if end and created > end:
                continue
            results.append(Entity.from_dict(edata))
        results.sort(key=lambda e: e.created_at, reverse=True)
        return results

    def search(self, query: str, etype: Optional[EntityType] = None, top_k: int = 10) -> List[Tuple[Entity, float]]:
        qemb = self.embeddings.embed(query)
        if not qemb:
            return []
        results = []
        for edata in self._state["entities"].values():
            if etype and edata.get("type") != etype.value:
                continue
            emb = edata.get("embedding")
            if not emb:
                continue
            sim = cosine_similarity(qemb, emb)
            if sim > 0.3:
                results.append((Entity.from_dict(edata), sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def mark_superseded(self, old_id: str, new_id: str) -> bool:
        if old_id not in self._state["entities"] or new_id not in self._state["entities"]:
            return False
        self.add_relation(new_id, old_id, RelationType.SUPERSEDES)
        self._state["entities"][old_id]["metadata"]["superseded_by"] = new_id
        self._save_state()
        return True

    def get_entity(self, eid: str) -> Optional[Entity]:
        if eid in self._state["entities"]:
            return Entity.from_dict(self._state["entities"][eid])
        return None

    def get_all_decisions(self, include_superseded: bool = False) -> List[Entity]:
        decisions = []
        for edata in self._state["entities"].values():
            if edata.get("type") != EntityType.DECISION.value:
                continue
            if not include_superseded and edata.get("metadata", {}).get("superseded_by"):
                continue
            decisions.append(Entity.from_dict(edata))
        decisions.sort(key=lambda e: e.created_at, reverse=True)
        return decisions

    def get_stats(self) -> Dict[str, Any]:
        type_counts = {}
        for edata in self._state["entities"].values():
            t = edata.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {"total_entities": len(self._state["entities"]), "total_relations": len(self._state["relations"]),
                "by_type": type_counts, "conflicts_detected": self._state["stats"].get("conflicts_detected", 0)}


def get_knowledge_graph(project_path: Optional[Path] = None) -> KnowledgeGraph:
    return KnowledgeGraph(project_path)
