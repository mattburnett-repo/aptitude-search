from app.core.models import Constraints
from app.job_discovery.discovery import build_discovery_queries


def test_build_discovery_queries_uses_core_skills_and_constraints(
    stage1_fixture: dict[str, object],
) -> None:
    constraints = Constraints(location="Toronto, ON", remote_preference="remote")
    queries = build_discovery_queries(stage1_fixture, constraints, max_queries=4)

    assert len(queries) == 4
    assert all("senior software engineer" in q for q in queries)
    assert all("Toronto, ON" in q for q in queries)
    assert all("remote" in q for q in queries)
    assert all(q.endswith("jobs") for q in queries)
    assert any("Python" in q for q in queries)
    assert any("Django" in q for q in queries)
    assert any("Vue" in q for q in queries)
    assert not any("Legacy modernization" in q for q in queries)


def test_build_discovery_queries_respects_max_queries(
    stage1_fixture: dict[str, object],
) -> None:
    queries = build_discovery_queries(stage1_fixture, Constraints(), max_queries=2)
    assert len(queries) == 2


def test_build_discovery_queries_omits_location_when_unset(
    stage1_fixture: dict[str, object],
) -> None:
    queries = build_discovery_queries(
        stage1_fixture,
        Constraints(),
        max_queries=1,
    )
    assert len(queries) == 1
    assert "Toronto" not in queries[0]
