"""Тесты auth/models.py — модель User и тарифные лимиты."""

from __future__ import annotations

from app.auth.models import PLAN_LIMITS, User, UserPlan


class TestUserPlan:
    """Тесты UserPlan enum."""

    def test_values(self) -> None:
        assert UserPlan.FREE.value == 'free'
        assert UserPlan.STANDARD.value == 'standard'
        assert UserPlan.PRO.value == 'pro'


class TestPlanLimits:
    """Тесты PLAN_LIMITS."""

    def test_free_limit(self) -> None:
        assert PLAN_LIMITS[UserPlan.FREE] == 5

    def test_standard_limit(self) -> None:
        assert PLAN_LIMITS[UserPlan.STANDARD] == 30

    def test_pro_unlimited(self) -> None:
        assert PLAN_LIMITS[UserPlan.PRO] is None


class TestUserProperties:
    """Тесты свойств User."""

    def test_can_optimize_free_under_limit(self) -> None:
        user = User(
            email='test-prop@example.com',
            hashed_password='x',
            plan=UserPlan.FREE,
            optimizations_used=3,
        )
        assert user.can_optimize is True

    def test_can_optimize_free_at_limit(self) -> None:
        user = User(
            email='test-prop2@example.com',
            hashed_password='x',
            plan=UserPlan.FREE,
            optimizations_used=5,
        )
        assert user.can_optimize is False

    def test_can_optimize_pro_unlimited(self) -> None:
        user = User(
            email='test-prop3@example.com',
            hashed_password='x',
            plan=UserPlan.PRO,
            optimizations_used=1000,
        )
        assert user.can_optimize is True

    def test_optimization_limit_free(self) -> None:
        user = User(
            email='test-prop4@example.com',
            hashed_password='x',
            plan=UserPlan.FREE,
        )
        assert user.optimization_limit == 5

    def test_optimization_limit_pro(self) -> None:
        user = User(
            email='test-prop5@example.com',
            hashed_password='x',
            plan=UserPlan.PRO,
        )
        assert user.optimization_limit is None
