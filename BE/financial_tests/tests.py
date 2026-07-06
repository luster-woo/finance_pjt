from unittest.mock import MagicMock

from django.test import TestCase

from .recommend_utils import calculate_recommendation_score_algorithm
from .views import _calculate_axes, _normalize_answers


# ──────────────────────────────────────────────────────────────
#  _normalize_answers
# ──────────────────────────────────────────────────────────────

class NormalizeAnswersTests(TestCase):
    """역방향 문항(Q2·Q6·Q9 = index 1·5·8) 반전 처리 검증"""

    def test_forward_items_pass_through(self):
        answers = [1, 3, 5, 4, 2, 3, 4, 5, 3, 1]
        result = _normalize_answers(answers)
        self.assertEqual(result[0], 1.0)   # Q1  정방향
        self.assertEqual(result[2], 5.0)   # Q3  정방향
        self.assertEqual(result[9], 1.0)   # Q10 정방향

    def test_reverse_items_are_inverted(self):
        # index 1·5·8 → 6 - value
        answers = [3, 1, 3, 3, 3, 1, 3, 3, 1, 3]
        result = _normalize_answers(answers)
        self.assertEqual(result[1], 5.0)   # 6 - 1 = 5
        self.assertEqual(result[5], 5.0)
        self.assertEqual(result[8], 5.0)

    def test_output_length_equals_input(self):
        answers = [3] * 10
        self.assertEqual(len(_normalize_answers(answers)), 10)

    def test_extreme_reverse_values(self):
        answers = [3, 5, 3, 3, 3, 5, 3, 3, 5, 3]
        result = _normalize_answers(answers)
        self.assertEqual(result[1], 1.0)   # 6 - 5 = 1
        self.assertEqual(result[5], 1.0)
        self.assertEqual(result[8], 1.0)


# ──────────────────────────────────────────────────────────────
#  _calculate_axes
# ──────────────────────────────────────────────────────────────

class CalculateAxesTests(TestCase):
    """4축 성향 코드(ARLN 스타일) 계산 검증"""

    def test_returns_all_keys(self):
        result = _calculate_axes([3] * 10)
        for key in ('risk', 'rational', 'longterm', 'active', 'code'):
            self.assertIn(key, result)

    def test_code_is_four_chars(self):
        result = _calculate_axes([3] * 10)
        self.assertEqual(len(result['code']), 4)

    def test_empty_answers_returns_empty_dict(self):
        self.assertEqual(_calculate_axes([]), {})

    def test_too_few_answers_returns_empty_dict(self):
        self.assertEqual(_calculate_axes([3] * 9), {})

    def test_aggressive_profile(self):
        # 공격형(A): Q1=5, Q2=1(역방향→고점), Q10=5
        # 이성형(R): Q5=5, Q6=1(역→고점), Q9=1(역→고점)
        # 장기형(L): Q3=5
        # 능동형(N): Q4=5, Q7=5, Q8=5
        answers = [5, 1, 5, 5, 5, 1, 5, 5, 1, 5]
        result = _calculate_axes(answers)
        self.assertEqual(result['code'], 'ARLN')

    def test_stable_profile(self):
        # 안정형(S): Q1=1, Q2=5(역→저점), Q10=1
        # 감정형(E): Q5=1, Q6=5(역→저점), Q9=5(역→저점)
        # 단기형(T): Q3=1
        # 수동형(P): Q4=1, Q7=1, Q8=1
        answers = [1, 5, 1, 1, 1, 5, 1, 1, 5, 1]
        result = _calculate_axes(answers)
        self.assertEqual(result['code'], 'SETP')

    def test_scores_in_range(self):
        result = _calculate_axes([3] * 10)
        for key in ('risk', 'rational', 'longterm', 'active'):
            self.assertGreaterEqual(result[key], 0)
            self.assertLessEqual(result[key], 100)


# ──────────────────────────────────────────────────────────────
#  calculate_recommendation_score_algorithm  (폴백 스코어링)
# ──────────────────────────────────────────────────────────────

def _mock_product(product_type='deposit'):
    p = MagicMock()
    p.product_type = product_type
    return p


def _mock_option(save_trm=12, interest_rate=3.5, max_interest_rate=4.0):
    opt = MagicMock()
    opt.save_trm = save_trm
    opt.interest_rate = interest_rate
    opt.max_interest_rate = max_interest_rate
    return opt


class RecommendScoreAlgorithmTests(TestCase):
    """폴백 스코어링 알고리즘 단위 테스트"""

    def test_returns_required_keys(self):
        result = calculate_recommendation_score_algorithm(
            30, '안정형', _mock_product(), _mock_option()
        )
        self.assertIn('score', result)
        self.assertIn('reason', result)
        self.assertIn('factors', result)

    def test_score_within_0_to_100(self):
        for result_type in ('안정형', '안정추구형', '위험중립형', '적극투자형', '공격투자형'):
            result = calculate_recommendation_score_algorithm(
                50, result_type, _mock_product(), _mock_option()
            )
            self.assertGreaterEqual(result['score'], 0)
            self.assertLessEqual(result['score'], 100)

    def test_stable_type_prefers_deposit_over_saving(self):
        opt = _mock_option()
        score_deposit = calculate_recommendation_score_algorithm(
            20, '안정형', _mock_product('deposit'), opt
        )
        score_saving = calculate_recommendation_score_algorithm(
            20, '안정형', _mock_product('saving'), opt
        )
        self.assertGreater(score_deposit['score'], score_saving['score'])

    def test_aggressive_type_prefers_saving_over_deposit(self):
        opt = _mock_option()
        score_deposit = calculate_recommendation_score_algorithm(
            80, '공격투자형', _mock_product('deposit'), opt
        )
        score_saving = calculate_recommendation_score_algorithm(
            80, '공격투자형', _mock_product('saving'), opt
        )
        self.assertGreater(score_saving['score'], score_deposit['score'])

    def test_higher_interest_yields_higher_score(self):
        product = _mock_product('deposit')
        low_opt  = _mock_option(save_trm=12, interest_rate=1.0, max_interest_rate=1.5)
        high_opt = _mock_option(save_trm=12, interest_rate=4.0, max_interest_rate=5.0)
        score_low  = calculate_recommendation_score_algorithm(50, '위험중립형', product, low_opt)
        score_high = calculate_recommendation_score_algorithm(50, '위험중립형', product, high_opt)
        self.assertGreater(score_high['score'], score_low['score'])

    def test_optimal_period_6_to_12_months(self):
        product = _mock_product('deposit')
        opt_12  = _mock_option(save_trm=12)
        opt_60  = _mock_option(save_trm=60)
        score_12 = calculate_recommendation_score_algorithm(50, '위험중립형', product, opt_12)
        score_60 = calculate_recommendation_score_algorithm(50, '위험중립형', product, opt_60)
        self.assertGreater(score_12['score'], score_60['score'])

    def test_reason_is_non_empty_string(self):
        result = calculate_recommendation_score_algorithm(
            50, '위험중립형', _mock_product(), _mock_option()
        )
        self.assertIsInstance(result['reason'], str)
        self.assertTrue(len(result['reason']) > 0)
