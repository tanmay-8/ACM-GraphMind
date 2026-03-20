"""High-performance graph retrieval service with adaptive hybrid ranking."""

from __future__ import annotations

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone
import time
import math
import heapq

from neo4j import GraphDatabase
from neo4j.time import DateTime

from config.settings import Settings
from services.graph.query_understanding import QueryUnderstanding, RetrievalMode


class GraphRetrieval:
    """Optimized graph retrieval with low-latency mode-aware queries."""

    SCORE_WEIGHTS = {
        "relevance": 0.30,
        "distance": 0.25,
        "centrality": 0.15,
        "recency": 0.15,
        "confidence": 0.10,
        "reinforcement": 0.05,
    }

    RECENCY_DECAY_LAMBDA = 0.08
    CENTRALITY_CACHE_TTL_SEC = 300

    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                Settings.NEO4J_URI,
                auth=(Settings.NEO4J_USER, Settings.NEO4J_PASSWORD),
            )
            self.driver.verify_connectivity()
        except Exception as error:
            print(f"Warning: Could not connect to Neo4j: {error}")
            self.driver = None

        self.query_understanding = QueryUnderstanding()
        self._centrality_cache: Dict[str, Tuple[float, Dict[str, float]]] = {}

    def retrieve(
        self,
        user_id: str,
        query: str,
        max_depth: int = 2,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Retrieve and rank graph nodes for a question."""
        if not self.driver:
            return [], 0.0

        start = time.time()
        try:
            with self.driver.session() as session:
                mode, recommended_depth = self.query_understanding.classify_query(query)
                depth, top_k = self._build_retrieval_plan(mode, query, max_depth, recommended_depth)
                start_date = self.query_understanding.extract_timeline(query)

                use_ensemble = self._should_use_ensemble(mode, query)
                if use_ensemble:
                    raw_nodes = self._execute_ensemble_retrieval(
                        session=session,
                        user_id=user_id,
                        primary_mode=mode,
                        start_date=start_date,
                        depth=depth,
                        top_k=top_k,
                    )
                else:
                    raw_nodes = self._execute_mode_based_retrieval(
                        session=session,
                        user_id=user_id,
                        mode=mode,
                        start_date=start_date,
                        depth=depth,
                        top_k=top_k,
                    )

                centrality = self._get_centrality_scores(session, user_id)
                ranked = self._score_and_rank_nodes(raw_nodes, query, centrality, top_k)
                return ranked, (time.time() - start) * 1000
        except Exception as error:
            print(f"Error during graph retrieval: {error}")
            return [], (time.time() - start) * 1000

    def _build_retrieval_plan(
        self,
        mode: RetrievalMode,
        query_text: str,
        requested_depth: int,
        recommended_depth: int,
    ) -> Tuple[int, int]:
        token_count = len((query_text or "").split())
        depth = max(1, min(3, max(requested_depth, recommended_depth)))

        if mode == RetrievalMode.DIRECT_LOOKUP:
            top_k = 45
            depth = min(depth, 2)
        elif mode == RetrievalMode.AGGREGATION:
            top_k = 70
            depth = min(depth, 2)
        else:
            top_k = 90
            depth = max(2, depth)

        if token_count >= 16:
            top_k += 20
        return depth, min(top_k, 140)

    def _should_use_ensemble(self, mode: RetrievalMode, query: str) -> bool:
        token_count = len((query or "").split())
        if mode == RetrievalMode.RELATIONAL_REASONING:
            return True
        return token_count >= 12

    def _execute_ensemble_retrieval(
        self,
        session,
        user_id: str,
        primary_mode: RetrievalMode,
        start_date: Optional[datetime],
        depth: int,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        modes = [primary_mode] + [m for m in RetrievalMode if m != primary_mode]
        mode_budget = {
            primary_mode: top_k,
        }
        for mode in modes:
            if mode != primary_mode:
                mode_budget[mode] = max(20, int(top_k * 0.55))

        merged: Dict[str, Dict[str, Any]] = {}
        for mode in modes:
            nodes = self._execute_mode_based_retrieval(
                session=session,
                user_id=user_id,
                mode=mode,
                start_date=start_date,
                depth=depth,
                top_k=mode_budget[mode],
            )
            for node in nodes:
                node_id = node.get("properties", {}).get("id")
                if not node_id:
                    continue
                if node_id not in merged:
                    node["mode_coverage"] = 1
                    merged[node_id] = node
                else:
                    merged[node_id]["mode_coverage"] = merged[node_id].get("mode_coverage", 1) + 1

        return list(merged.values())

    def _execute_mode_based_retrieval(
        self,
        session,
        user_id: str,
        mode: RetrievalMode,
        start_date: Optional[datetime],
        depth: int,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        params = {
            "user_id": user_id,
            "top_k": top_k,
            "start_date": start_date,
        }
        node_time_filter = "AND ($start_date IS NULL OR coalesce(n.timestamp, n.last_reinforced, n.created_at) >= $start_date)"

        if mode == RetrievalMode.DIRECT_LOOKUP:
            query = f"""
            MATCH (u:User {{id: $user_id}})
            OPTIONAL MATCH (u)-[:OWNS_MESSAGE]->(m:Message)
            WHERE m.user_id = $user_id
            OPTIONAL MATCH (u)-[:MADE_TRANSACTION]->(t:Transaction)
            WHERE t.user_id = $user_id AND coalesce(t.superseded, false) = false
            OPTIONAL MATCH (t)-[:AFFECTS_ASSET]->(a:Asset)
            WHERE a.user_id = $user_id
            OPTIONAL MATCH (m)-[:DERIVED_FACT]->(f:Fact)
            WHERE f.user_id = $user_id
            WITH collect(DISTINCT m) + collect(DISTINCT t) + collect(DISTINCT a) + collect(DISTINCT f) as nodes
            UNWIND nodes as n
            WHERE n IS NOT NULL {node_time_filter}
            WITH n,
                CASE
                    WHEN n:Message THEN 1
                    WHEN n:Transaction THEN 1
                    WHEN n:Asset THEN 2
                    WHEN n:Fact THEN 2
                    ELSE {depth} + 1
                END AS hops,
                CASE
                    WHEN n:Fact THEN 'fact_memory'
                    WHEN n:Transaction THEN 'transaction_link'
                    WHEN n:Asset THEN 'asset_link'
                    WHEN n:Message THEN 'message_context'
                    ELSE 'direct_lookup'
                END AS matched_by
            RETURN DISTINCT n, hops, matched_by
            ORDER BY hops ASC
            LIMIT $top_k
            """
        elif mode == RetrievalMode.AGGREGATION:
            query = f"""
            MATCH (u:User {{id: $user_id}})
            MATCH (u)-[:MADE_TRANSACTION]->(t:Transaction)
            WHERE t.user_id = $user_id
              AND coalesce(t.superseded, false) = false
              AND ($start_date IS NULL OR coalesce(t.timestamp, t.last_reinforced, t.created_at) >= $start_date)
            OPTIONAL MATCH (t)-[:AFFECTS_ASSET]->(a:Asset)
            WHERE a.user_id = $user_id
            OPTIONAL MATCH (f:Fact)-[:CONFIRMS]->(t)
            WHERE f.user_id = $user_id
            WITH collect(DISTINCT t) + collect(DISTINCT a) + collect(DISTINCT f) as nodes
            UNWIND nodes as n
            WHERE n IS NOT NULL {node_time_filter}
            WITH n,
                CASE
                    WHEN n:Transaction THEN 1
                    WHEN n:Asset THEN 2
                    WHEN n:Fact THEN 2
                    ELSE {depth} + 1
                END AS hops,
                CASE
                    WHEN n:Transaction THEN 'aggregation_transaction'
                    WHEN n:Fact THEN 'aggregation_fact'
                    WHEN n:Asset THEN 'aggregation_asset'
                    ELSE 'aggregation_context'
                END AS matched_by
            RETURN DISTINCT n, hops, matched_by
            ORDER BY hops ASC
            LIMIT $top_k
            """
        else:
            query = f"""
            MATCH (u:User {{id: $user_id}})
            OPTIONAL MATCH (u)-[:MADE_TRANSACTION]->(t:Transaction)-[:AFFECTS_ASSET]->(a:Asset)
            WHERE t.user_id = $user_id
              AND a.user_id = $user_id
              AND coalesce(t.superseded, false) = false
              AND ($start_date IS NULL OR coalesce(t.timestamp, t.last_reinforced, t.created_at) >= $start_date)
            OPTIONAL MATCH (a)-[:CONTRIBUTES_TO]->(g:Goal)
            WHERE g.user_id = $user_id
            OPTIONAL MATCH (u)-[:HAS_PREFERENCE]->(p:Preference)
            WHERE p.user_id = $user_id
            OPTIONAL MATCH (f:Fact)-[:CONFIRMS]->(t)
            WHERE f.user_id = $user_id
            OPTIONAL MATCH (f2:Fact)-[:RELATES_TO]->(a)
            WHERE f2.user_id = $user_id
            WITH collect(DISTINCT t) + collect(DISTINCT a) + collect(DISTINCT g) + collect(DISTINCT p) + collect(DISTINCT f) + collect(DISTINCT f2) as nodes
            UNWIND nodes as n
            WHERE n IS NOT NULL {node_time_filter}
            WITH n,
                CASE
                    WHEN n:Preference THEN 1
                    WHEN n:Transaction THEN 1
                    WHEN n:Asset THEN 2
                    WHEN n:Fact THEN 2
                    WHEN n:Goal THEN 3
                    ELSE {depth} + 1
                END AS hops,
                CASE
                    WHEN n:Goal THEN 'goal_reasoning'
                    WHEN n:Preference THEN 'preference_reasoning'
                    WHEN n:Asset THEN 'asset_reasoning'
                    WHEN n:Fact THEN 'fact_reasoning'
                    ELSE 'relational_context'
                END AS matched_by
            RETURN DISTINCT n, hops, matched_by
            ORDER BY hops ASC
            LIMIT $top_k
            """

        result = session.run(query, **params)
        nodes: List[Dict[str, Any]] = []
        for record in result:
            node = record.get("n")
            if not node:
                continue
            nodes.append(
                {
                    "type": list(node.labels)[0] if node.labels else "Unknown",
                    "properties": self._serialize_neo4j_types(dict(node)),
                    "neo4j_id": node.id,
                    "hop_distance": int(record.get("hops", depth + 1)),
                    "retrieval_trace": {
                        "mode": mode.value,
                        "matched_by": record.get("matched_by", "unknown"),
                        "depth_used": depth,
                        "top_k_used": top_k,
                        "timeline_filter_applied": start_date is not None,
                    },
                }
            )
        return nodes

    def _get_centrality_scores(self, session, user_id: str) -> Dict[str, float]:
        now = time.time()
        cached = self._centrality_cache.get(user_id)
        if cached and (now - cached[0] < self.CENTRALITY_CACHE_TTL_SEC):
            return cached[1]

        try:
            result = session.run(
                """
                MATCH (n {user_id: $user_id})
                WHERE n.id IS NOT NULL
                OPTIONAL MATCH (n)--(m {user_id: $user_id})
                WITH n, count(m) as degree
                RETURN n.id as node_id,
                    CASE
                        WHEN degree <= 0 THEN 0.0
                        ELSE min(1.0, log(1 + toFloat(degree)) / log(50.0))
                    END as centrality
                """,
                user_id=user_id,
            )
            scores = {r.get("node_id"): float(r.get("centrality", 0.0)) for r in result if r.get("node_id")}
            self._centrality_cache[user_id] = (now, scores)
            return scores
        except Exception:
            return {}

    def _score_and_rank_nodes(
        self,
        nodes: List[Dict[str, Any]],
        query: str,
        centrality_scores: Dict[str, float],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        keywords = self.query_understanding.extract_query_keywords(query)

        scored: List[Dict[str, Any]] = []
        for node in nodes:
            props = node.get("properties", {})
            node_type = node.get("type", "Unknown")
            if node_type == "User":
                continue

            hops = int(node.get("hop_distance", 3))
            distance_score = 1.0 / (hops + 1)
            relevance_score = self._calculate_relevance_score(node, keywords, query.lower())

            node_id = props.get("id")
            centrality_score = centrality_scores.get(node_id, 0.05)

            recency_score = 0.45
            days_ago = 0.0
            reference_ts = props.get("last_reinforced") or props.get("timestamp") or props.get("created_at")
            if isinstance(reference_ts, str):
                try:
                    ts = datetime.fromisoformat(reference_ts.replace("Z", "+00:00"))
                    days_ago = max(0.0, (now - ts).total_seconds() / 86400)
                    recency_score = math.exp(-self.RECENCY_DECAY_LAMBDA * days_ago)
                except Exception:
                    pass

            confidence = float(props.get("confidence", 0.5))
            reinforcement_count = int(props.get("reinforcement_count", 0))
            reinforcement_score = min(1.0, math.log(1 + reinforcement_count) / math.log(10)) if reinforcement_count > 0 else 0.0

            mode_coverage = float(node.get("mode_coverage", 1))
            mode_boost = min(1.0, mode_coverage / 3.0)

            score = (
                self.SCORE_WEIGHTS["relevance"] * relevance_score
                + self.SCORE_WEIGHTS["distance"] * distance_score
                + self.SCORE_WEIGHTS["centrality"] * centrality_score
                + self.SCORE_WEIGHTS["recency"] * recency_score
                + self.SCORE_WEIGHTS["confidence"] * confidence
                + self.SCORE_WEIGHTS["reinforcement"] * reinforcement_score
            )
            score *= 1.0 + 0.15 * mode_boost
            score = min(1.0, score)

            node["retrieval_score"] = round(score, 4)
            node["score_breakdown"] = {
                "relevance": round(relevance_score, 4),
                "distance": round(distance_score, 4),
                "centrality": round(centrality_score, 4),
                "recency": round(recency_score, 4),
                "confidence": round(confidence, 4),
                "reinforcement": round(reinforcement_score, 4),
                "mode_coverage": int(mode_coverage),
                "days_since_reference": round(days_ago, 3),
                "hop_distance": hops,
                "trace": node.get("retrieval_trace", {}),
            }
            node["snippet"] = self._create_snippet(node_type, props)

            if score >= 0.08:
                scored.append(node)

        return heapq.nlargest(top_k, scored, key=lambda x: x.get("retrieval_score", 0.0))

    def _calculate_relevance_score(
        self,
        node: Dict[str, Any],
        query_keywords: List[str],
        query_lower: str,
    ) -> float:
        if not query_keywords:
            return 0.5

        props = node.get("properties", {})
        fields = []
        for key in ["name", "text", "transaction_type", "asset_type", "description"]:
            value = props.get(key)
            if isinstance(value, str) and value:
                fields.append(value.lower())

        if not fields:
            return 0.2

        matched = 0
        for keyword in query_keywords:
            if any(keyword in field for field in fields):
                matched += 1

        exact_phrase_boost = 0.1 if any(query_lower[:24] in field for field in fields if len(query_lower) >= 8) else 0.0
        return min(1.0, matched / max(1, len(query_keywords)) + exact_phrase_boost)

    def _create_snippet(self, node_type: str, props: Dict[str, Any]) -> str:
        if node_type == "Transaction":
            amount = props.get("amount", 0)
            tx_type = props.get("transaction_type", "transaction")
            try:
                return f"{tx_type.capitalize()} of Rs {float(amount):,.0f}"
            except Exception:
                return f"{tx_type.capitalize()} transaction"
        if node_type == "Asset":
            return f"{props.get('name', 'Unknown')} ({props.get('asset_type', 'asset')})"
        if node_type == "Fact":
            text = props.get("text", "")
            return text[:70] + "..." if len(text) > 70 else text
        if node_type == "Goal":
            return f"Goal: {props.get('name', 'Unknown goal')}"
        if node_type == "Message":
            text = props.get("text", "")
            return text[:60] + "..." if len(text) > 60 else text
        return props.get("name", props.get("text", node_type))

    def _serialize_neo4j_types(self, obj: Any) -> Any:
        if isinstance(obj, DateTime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize_neo4j_types(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize_neo4j_types(x) for x in obj]
        return obj

    def reinforce_cited_nodes(self, user_id: str, node_ids: List[str]):
        if not self.driver or not node_ids:
            return
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    UNWIND $node_ids as node_id
                    MATCH (n {id: node_id, user_id: $user_id})
                    SET n.last_reinforced = datetime(),
                        n.reinforcement_count = coalesce(n.reinforcement_count, 0) + 1
                    RETURN count(n) as updated_count
                    """,
                    user_id=user_id,
                    node_ids=node_ids,
                )
                record = result.single()
                count = record["updated_count"] if record else 0
                print(f"Reinforced {count} cited nodes")
        except Exception as error:
            print(f"Error reinforcing nodes: {error}")

    def close(self):
        if self.driver:
            self.driver.close()
