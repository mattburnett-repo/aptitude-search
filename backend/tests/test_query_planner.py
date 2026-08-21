from app.core.models import Constraints
from app.job_discovery.discovery import build_discovery_queries

_SOFTWARE_ENGINEER = "software engineer"


def test_build_discovery_queries_uses_adjacent_roles_and_constraints(
    stage1_fixture: dict[str, object],
) -> None:
    constraints = Constraints(location="Toronto, ON", remote_preference="remote")
    queries = build_discovery_queries(stage1_fixture, constraints, max_queries=4)

    assert len(queries) == 4
    assert all("Toronto, ON" in q for q in queries)
    assert all("remote" in q for q in queries)
    assert all(q.endswith("jobs") for q in queries)
    assert any("Solutions Engineer" in q for q in queries)
    assert any("Platform Engineer" in q for q in queries)
    assert any("Technical Program Manager" in q for q in queries)
    assert any("Logistics" in q for q in queries)
    assert not any("Python" in q for q in queries)
    assert not any("Django" in q for q in queries)
    assert not any(_SOFTWARE_ENGINEER in q.lower() for q in queries)
    assert not any("mission-driven" in q.lower() for q in queries)


def test_build_discovery_queries_respects_max_queries(
    stage1_fixture: dict[str, object],
) -> None:
    queries = build_discovery_queries(stage1_fixture, Constraints(), max_queries=2)
    assert len(queries) == 2
    assert any("Solutions Engineer" in q for q in queries)
    assert any("Technical Program Manager" in q for q in queries)


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
    assert "Solutions Engineer" in queries[0]


def test_build_discovery_queries_falls_back_to_core_skills_without_swe_title() -> None:
    profile: dict[str, object] = {
        "seniority_band": "senior",
        "adjacent_roles": [],
        "domains": [],
        "core_skills": [{"name": "Python", "confidence": "high"}],
        "secondary_skills": [{"name": "PostgreSQL", "confidence": "high"}],
    }
    queries = build_discovery_queries(profile, Constraints(), max_queries=2)

    assert len(queries) == 2
    assert not any(_SOFTWARE_ENGINEER in q.lower() for q in queries)
    assert any("senior Python jobs" in q for q in queries)
    assert any("senior PostgreSQL jobs" in q for q in queries)


def test_build_discovery_queries_uses_role_family_plan(
    stage1_fixture: dict[str, object],
    role_family_plan_fixture: dict[str, object],
) -> None:
    constraints = Constraints(location="Toronto, ON", remote_preference="remote")
    queries = build_discovery_queries(
        stage1_fixture,
        constraints,
        role_family_plan=role_family_plan_fixture,
        max_queries=6,
    )

    assert len(queries) == 6
    assert any("solutions engineer" in q.lower() for q in queries)
    assert any("platform engineer" in q.lower() for q in queries)
    assert any("technical program manager" in q.lower() for q in queries)
    assert not any("Python" in q for q in queries)
    assert not any(_SOFTWARE_ENGINEER in q.lower() for q in queries)


def test_build_discovery_queries_non_swe_profile_uses_plan_not_software_engineer() -> None:
    profile: dict[str, object] = {
        "seniority_band": "executive",
        "adjacent_roles": [
            {
                "label": "Director, Revenue Operations",
                "confidence": "high",
            }
        ],
        "domains": [
            {
                "label": "Healthcare marketing technology",
                "confidence": "high",
            }
        ],
        "core_skills": [{"name": "HubSpot", "confidence": "high"}],
        "secondary_skills": [],
    }
    plan: dict[str, object] = {
        "recommended_role_families": [
            {
                "role_family": "Marketing Operations / RevOps",
                "fit_reason": "CRM and campaign operations leadership.",
                "supporting_signals": ["HubSpot", "Salesforce"],
                "work_modes": ["campaign operations", "lifecycle marketing"],
                "search_terms": [
                    "marketing operations director",
                    "director marketing operations",
                ],
                "avoid_terms": ["software engineer"],
            },
            {
                "role_family": "Revenue Operations",
                "fit_reason": "Sales and marketing systems alignment.",
                "supporting_signals": ["lead scoring"],
                "work_modes": ["revops", "sales enablement"],
                "search_terms": ["revenue operations manager"],
                "avoid_terms": ["account executive"],
            },
        ],
        "rationale": ["Healthcare martech leadership path."],
    }
    constraints = Constraints(location="Chicago, IL", remote_preference="hybrid")
    queries = build_discovery_queries(
        profile,
        constraints,
        role_family_plan=plan,
        max_queries=4,
    )

    assert queries
    assert any("marketing operations" in q.lower() for q in queries)
    assert not any(_SOFTWARE_ENGINEER in q.lower() for q in queries)
    assert not any("HubSpot" in q for q in queries)


def test_build_discovery_queries_uses_interests_when_no_roles_or_domains() -> None:
    profile: dict[str, object] = {
        "seniority_band": "mid",
        "adjacent_roles": [],
        "domains": [],
        "interests": [{"label": "climate", "confidence": "medium"}],
        "core_skills": [{"name": "Python", "confidence": "high"}],
        "secondary_skills": [],
    }
    queries = build_discovery_queries(profile, Constraints(), max_queries=2)

    assert any("climate" in q.lower() for q in queries)
    assert not any("Python" in q for q in queries)
    assert not any("mission-driven" in q.lower() for q in queries)


def test_build_discovery_queries_prefers_high_onet_aligned_families(
    stage1_fixture: dict[str, object],
) -> None:
    plan: dict[str, object] = {
        "recommended_role_families": [
            {
                "role_family": "Data Science",
                "fit_reason": "Weak path.",
                "supporting_signals": ["Python"],
                "work_modes": ["modeling"],
                "search_terms": ["data scientist", "machine learning engineer"],
                "avoid_terms": ["quota"],
            },
            {
                "role_family": "Product Engineering",
                "fit_reason": "Strong path.",
                "supporting_signals": ["TypeScript"],
                "work_modes": ["customer-facing tools"],
                "search_terms": [
                    "product engineer",
                    "full stack engineer",
                    "software engineer",
                ],
                "avoid_terms": ["data scientist"],
            },
        ],
        "rationale": ["Prefer product engineering."],
    }
    occupation_matches: list[dict[str, object]] = [
        {"title": "Software Developers", "score": 0.82, "onetsoc_code": "15-1252.00"},
        {"title": "Web Developers", "score": 0.71, "onetsoc_code": "15-1254.00"},
        {"title": "Data Scientists", "score": 0.51, "onetsoc_code": "15-2051.00"},
    ]
    queries = build_discovery_queries(
        stage1_fixture,
        Constraints(),
        role_family_plan=plan,
        occupation_matches=occupation_matches,
        max_queries=3,
    )

    assert len(queries) == 3
    assert any("product engineer" in q.lower() for q in queries)
    assert any("full stack engineer" in q.lower() for q in queries)
    assert not any("data scientist" in q.lower() for q in queries)
    assert not any("machine learning" in q.lower() for q in queries)
