"""Neo4j connection (AuraDB Free). Credentials come from `.env`.

Certificates are verified against certifi's CA bundle instead of the operating system store: Aura's
certificate chains up to an SSL.com root that Windows only installs on demand (for browsers), so Python
on a fresh Windows machine rejects it as "self-signed". Verification stays fully on.

Usage (from repo root): python -m src.kg.graph_db   # connectivity check: server version and graph size
"""

from functools import lru_cache

import certifi
from neo4j import Driver, GraphDatabase, TrustCustomCAs

from src.settings import get_settings


@lru_cache
def get_driver() -> Driver:
    s = get_settings()
    if not (s.neo4j_uri and s.neo4j_password):
        raise SystemExit("Set NEO4J_URI and NEO4J_PASSWORD in .env")
    # "neo4j+s://" fixes the trust store; plain "neo4j://" + encrypted=True lets us choose it (certifi).
    uri = s.neo4j_uri.replace("neo4j+s://", "neo4j://")
    driver = GraphDatabase.driver(uri, auth=(s.neo4j_username, s.neo4j_password.get_secret_value()),
                                  encrypted=True, trusted_certificates=TrustCustomCAs(certifi.where()))
    driver.verify_connectivity()
    return driver


if __name__ == "__main__":
    s = get_settings()
    info = get_driver().get_server_info()
    records, _, _ = get_driver().execute_query(
        "MATCH (n) WITH count(n) AS nodes OPTIONAL MATCH ()-[r]->() RETURN nodes, count(r) AS relationships",
        database_=s.neo4j_database)
    print(f"Connected to {info.address} ({info.agent}) | database {s.neo4j_database} "
          f"| {records[0]['nodes']} nodes, {records[0]['relationships']} relationships")
