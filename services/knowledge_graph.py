"""Knowledge graph utilities using NetworkX.

Functions:
- build_graph_from_db(session): builds a DiGraph from SkillRelationship rows
- get_prerequisites(graph, skill_name): immediate prerequisite skill names
- get_all_prerequisites(graph, skill_name): full prerequisite closure
- shortest_path(graph, source_name, target_name): shortest path list or None
"""
import networkx as nx
from typing import List, Optional


def build_graph_from_db(session):
    """Build a NetworkX DiGraph from the database SkillRelationship table.

    Nodes are skill names. Edges are from source -> target with attributes
    `relationship_type` and `strength`.
    """
    from models.skill import SkillRelationship, Skill

    G = nx.DiGraph()
    skills = {s.id: s.name for s in session.query(Skill).all()}
    rels = session.query(SkillRelationship).all()
    for r in rels:
        src_name = skills.get(r.source_skill_id)
        tgt_name = skills.get(r.target_skill_id)
        if not src_name or not tgt_name:
            continue
        if not G.has_node(src_name):
            G.add_node(src_name)
        if not G.has_node(tgt_name):
            G.add_node(tgt_name)
        G.add_edge(src_name, tgt_name, relationship_type=r.relationship_type, strength=float(r.strength or 1.0))
    return G


def get_prerequisites(G: nx.DiGraph, skill_name: str) -> List[str]:
    """Return immediate prerequisite skill names for `skill_name`.
    Looks for incoming edges with `relationship_type == 'prerequisite'`.
    """
    if skill_name not in G:
        return []
    preds = []
    for u, v, data in G.in_edges(skill_name, data=True):
        if data.get('relationship_type') == 'prerequisite':
            preds.append(u)
    return preds


def get_all_prerequisites(G: nx.DiGraph, skill_name: str) -> List[str]:
    """Return all prerequisite ancestors (transitive closure) for `skill_name`.
    Only follows edges regardless of relationship_type, but filters nodes that can reach `skill_name`.
    """
    if skill_name not in G:
        return []
    # ancestors in directed graph
    ancestors = nx.ancestors(G, skill_name)
    return list(ancestors)


def shortest_path(G: nx.DiGraph, source_name: str, target_name: str) -> Optional[List[str]]:
    """Return the shortest path from source_name to target_name if exists, else None."""
    try:
        path = nx.shortest_path(G, source=source_name, target=target_name)
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

