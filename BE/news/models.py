from django.db import models


class News(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WeeklyBriefing(models.Model):
    """주간 AI 금융 브리핑 (성향 유형별 × 주 1회 생성)"""
    week_start = models.DateField()          # 해당 주 월요일
    financial_type = models.CharField(max_length=50, blank=True)  # 빈 문자열 = 일반(비회원)
    economy_summary = models.JSONField(default=list)  # 경제 3줄 요약 [{title, desc}, ...]
    actions = models.JSONField(default=list)          # 성향별 행동 추천 [str, ...]
    tip = models.TextField(blank=True)                # 이번 주 금융 TIP
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('week_start', 'financial_type')
        ordering = ['-week_start']
