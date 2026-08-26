import europagrad_agent
from europagrad_agent.cli import ALL_COUNTRIES, SEED_COUNTRIES
from europagrad_agent.taxonomy import ALL_ENUMS, DeadlineStatus, FundingClass


def test_package_version() -> None:
    assert europagrad_agent.__version__ == "0.1.0"


def test_seed_countries_supported() -> None:
    for code in SEED_COUNTRIES:
        assert code in ALL_COUNTRIES


def test_taxonomy_values_stable() -> None:
    assert FundingClass.FULLY_FUNDED != FundingClass.TUITION_FREE
    assert DeadlineStatus("CLOSED") == DeadlineStatus.CLOSED


def test_taxonomy_covers_all_postgres_enums() -> None:
    expected = {
        "funding_class",
        "opportunity_type",
        "source_tier",
        "match_class",
        "scholarship_match",
        "deadline_status",
        "job_status",
        "tracker_status",
    }
    assert set(ALL_ENUMS) == expected


def test_taxonomy_no_duplicate_values_within_enum() -> None:
    for name, enum_cls in ALL_ENUMS.items():
        values = [member.value for member in enum_cls]
        assert len(values) == len(set(values)), f"duplicate values in {name}"
