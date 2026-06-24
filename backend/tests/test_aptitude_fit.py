import pytest

from app.core.validate import validate_stage
from app.job_discovery.aptitude_fit import rank_and_filter_found_jobs, score_job_aptitude_fit


def test_role_family_plan_fixture_validates(role_family_plan_fixture: dict[str, object]) -> None:
    validate_stage("roleFamilyPlan", role_family_plan_fixture)


def test_score_job_aptitude_fit_rejects_avoid_terms(
    stage1_fixture: dict[str, object],
    role_family_plan_fixture: dict[str, object],
) -> None:
    job = {
        "title": "Account Executive",
        "company": "SaaS Co",
        "url": "https://example.com/jobs/account-executive",
    }
    score, signals = score_job_aptitude_fit(
        job,
        stage1_fixture,
        role_family_plan=role_family_plan_fixture,
    )
    assert score < 0
    assert any(signal.startswith("avoid:") for signal in signals)


def test_score_job_aptitude_fit_rewards_integration_title(
    stage1_fixture: dict[str, object],
    role_family_plan_fixture: dict[str, object],
) -> None:
    job = {
        "title": "Solutions Engineer - Integrations",
        "company": "Logistics SaaS",
        "url": "https://example.com/jobs/solutions-engineer",
    }
    score, signals = score_job_aptitude_fit(
        job,
        stage1_fixture,
        role_family_plan=role_family_plan_fixture,
    )
    assert score >= 2
    assert signals


def test_rank_and_filter_found_jobs_orders_by_fit(
    stage1_fixture: dict[str, object],
    role_family_plan_fixture: dict[str, object],
) -> None:
    jobs = [
        {
            "title": "Software Engineer",
            "company": "Generic Corp",
            "url": "https://example.com/jobs/software-engineer",
        },
        {
            "title": "Platform Engineer - Internal Tools",
            "company": "DevTools Inc",
            "url": "https://example.com/jobs/platform-engineer",
        },
        {
            "title": "Account Executive",
            "company": "Sales Co",
            "url": "https://example.com/jobs/account-executive",
        },
    ]
    ranked = rank_and_filter_found_jobs(
        jobs,
        stage1_fixture,
        role_family_plan=role_family_plan_fixture,
    )
    assert len(ranked) == 1
    assert ranked[0]["title"] == "Platform Engineer - Internal Tools"
    assert ranked[0].get("aptitude_fit_signals")
