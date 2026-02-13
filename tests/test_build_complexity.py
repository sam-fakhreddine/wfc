"""
Tests for WFC Build Complexity Assessor

Verifies PROP-006: Deterministic complexity assessment
"""

import pytest
from wfc.scripts.skills.build.complexity_assessor import ComplexityAssessor, ComplexityRating
from wfc.scripts.skills.build.interview import InterviewResult


class TestComplexityAssessor:
    """Test complexity assessment algorithm"""

    def setup_method(self):
        """Setup test fixtures"""
        self.assessor = ComplexityAssessor()

    def test_s_complexity_single_file_small(self):
        """TEST-005: S rating for single file, <50 LOC, no deps"""
        interview = InterviewResult(
            feature_description="Add logging",
            scope="single_file",
            files_affected=["middleware.py"],
            loc_estimate=25,
            new_dependencies=[],
            constraints=[],
        )

        rating = self.assessor.assess(interview)

        assert rating.rating == "S"
        assert rating.agent_count == 1
        assert "Simple change" in rating.rationale

    def test_m_complexity_few_files(self):
        """TEST-006: M rating for 2-3 files, 50-200 LOC"""
        interview = InterviewResult(
            feature_description="Add JWT auth",
            scope="few_files",
            files_affected=["auth.py", "middleware.py"],
            loc_estimate=150,
            new_dependencies=["pyjwt"],
            constraints=["security"],
        )

        rating = self.assessor.assess(interview)

        assert rating.rating == "M"
        assert rating.agent_count in [1, 2]
        assert "Medium change" in rating.rationale

    def test_l_complexity_new_module(self):
        """TEST-007: L rating for new module, 200-500 LOC"""
        interview = InterviewResult(
            feature_description="Refactor user module",
            scope="new_module",
            files_affected=[
                "users/__init__.py",
                "users/models.py",
                "users/service.py",
                "users/repository.py",
                "users/api.py",
            ],
            loc_estimate=400,
            new_dependencies=[],
            constraints=["maintain_api_compatibility"],
        )

        rating = self.assessor.assess(interview)

        assert rating.rating == "L"
        assert rating.agent_count in [2, 3]
        assert "Large change" in rating.rationale

    def test_xl_complexity_triggers_recommendation(self):
        """TEST-008: XL rating triggers wfc-plan recommendation"""
        interview = InterviewResult(
            feature_description="Complete system rewrite",
            scope="many_files",
            files_affected=[f"file{i}.py" for i in range(15)],
            loc_estimate=800,
            new_dependencies=["fastapi", "sqlalchemy"],
            constraints=[],
        )

        rating = self.assessor.assess(interview)

        assert rating.rating == "XL"
        assert rating.recommendation != ""
        assert "wfc-plan" in rating.recommendation.lower()

    def test_deterministic_assessment(self):
        """TEST-009: Same interview → same rating (PROP-006)"""
        interview = InterviewResult(
            feature_description="Add rate limiting",
            scope="few_files",
            files_affected=["api.py", "middleware.py"],
            loc_estimate=100,
            new_dependencies=["redis"],
            constraints=[],
        )

        # Run assessment 10 times
        ratings = [self.assessor.assess(interview) for _ in range(10)]

        # All should be identical
        first = ratings[0]
        for rating in ratings[1:]:
            assert rating.rating == first.rating
            assert rating.agent_count == first.agent_count
            assert rating.rationale == first.rationale

    def test_boundary_s_to_m(self):
        """Test boundary between S and M complexity"""
        # Just over S threshold
        interview = InterviewResult(
            feature_description="Small feature",
            scope="few_files",
            files_affected=["file1.py", "file2.py"],
            loc_estimate=60,
            new_dependencies=[],
            constraints=[],
        )

        rating = self.assessor.assess(interview)
        assert rating.rating == "M"

    def test_boundary_m_to_l(self):
        """Test boundary between M and L complexity"""
        # Just over M threshold
        interview = InterviewResult(
            feature_description="Medium feature",
            scope="few_files",
            files_affected=[f"file{i}.py" for i in range(4)],
            loc_estimate=250,
            new_dependencies=[],
            constraints=[],
        )

        rating = self.assessor.assess(interview)
        assert rating.rating == "L"

    def test_boundary_l_to_xl(self):
        """Test boundary between L and XL complexity"""
        # Just over L threshold
        interview = InterviewResult(
            feature_description="Large feature",
            scope="many_files",
            files_affected=[f"file{i}.py" for i in range(12)],
            loc_estimate=600,
            new_dependencies=[],
            constraints=[],
        )

        rating = self.assessor.assess(interview)
        assert rating.rating == "XL"
