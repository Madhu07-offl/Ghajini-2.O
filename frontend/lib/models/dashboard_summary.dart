class WeeklyDayHistory {
  final String day;
  final String date;
  final int done;
  final int missed;

  WeeklyDayHistory({
    required this.day,
    required this.date,
    required this.done,
    required this.missed,
  });

  factory WeeklyDayHistory.fromJson(Map<String, dynamic> json) {
    return WeeklyDayHistory(
      day: json['day'] ?? '',
      date: json['date'] ?? '',
      done: json['done'] ?? 0,
      missed: json['missed'] ?? 0,
    );
  }
}

class TopQuestion {
  final String question;
  final int count;

  TopQuestion({
    required this.question,
    required this.count,
  });

  factory TopQuestion.fromJson(Map<String, dynamic> json) {
    return TopQuestion(
      question: json['question'] ?? '',
      count: json['count'] ?? 1,
    );
  }
}

class DashboardSummary {
  final double adherencePct;
  final int doneCount;
  final int missedCount;
  final int totalReminders7d;
  final int alertsCount;
  final int recognitionsToday;
  final List<TopQuestion> topQuestions;
  final String? lastActivity;
  final List<WeeklyDayHistory> weeklyHistory;

  DashboardSummary({
    required this.adherencePct,
    required this.doneCount,
    required this.missedCount,
    required this.totalReminders7d,
    required this.alertsCount,
    required this.recognitionsToday,
    required this.topQuestions,
    this.lastActivity,
    required this.weeklyHistory,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    final rawTop = json['top_questions'] as List? ?? [];
    final rawWeekly = json['weekly_history'] as List? ?? [];

    return DashboardSummary(
      adherencePct: (json['adherence_pct'] as num?)?.toDouble() ?? 100.0,
      doneCount: json['done_count'] ?? 0,
      missedCount: json['missed_count'] ?? 0,
      totalReminders7d: json['total_reminders_7d'] ?? 0,
      alertsCount: json['alerts_count'] ?? 0,
      recognitionsToday: json['recognitions_today'] ?? 0,
      topQuestions: rawTop.map((q) => TopQuestion.fromJson(q)).toList(),
      lastActivity: json['last_activity'],
      weeklyHistory: rawWeekly.map((w) => WeeklyDayHistory.fromJson(w)).toList(),
    );
  }
}

class DailySummary {
  final String summary;
  final String source;
  final Map<String, dynamic> details;

  DailySummary({
    required this.summary,
    required this.source,
    required this.details,
  });

  factory DailySummary.fromJson(Map<String, dynamic> json) {
    return DailySummary(
      summary: json['summary'] ?? 'Mother took her scheduled morning care, met family, and had no distress events today.',
      source: json['source'] ?? 'template',
      details: json['details'] ?? {},
    );
  }
}
