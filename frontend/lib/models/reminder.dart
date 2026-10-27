class Reminder {
  final int id;
  final int patientId;
  final String title;
  final String scheduledTime;
  final String frequency;
  final String status;
  final int retryCount;
  final DateTime? lastTriggeredAt;
  final DateTime createdAt;

  Reminder({
    required this.id,
    required this.patientId,
    required this.title,
    required this.scheduledTime,
    required this.frequency,
    required this.status,
    required this.retryCount,
    this.lastTriggeredAt,
    required this.createdAt,
  });

  factory Reminder.fromJson(Map<String, dynamic> json) {
    return Reminder(
      id: (json['id'] as num).toInt(),
      patientId: ((json['patient_id'] ?? 1) as num).toInt(),
      title: json['title'] as String? ?? 'Reminder',
      scheduledTime: json['scheduled_time'] as String? ?? '09:00',
      frequency: json['frequency'] as String? ?? 'daily',
      status: json['status'] as String? ?? 'pending',
      retryCount: (json['retry_count'] as num?)?.toInt() ?? 0,
      lastTriggeredAt: json['last_triggered_at'] != null
          ? DateTime.tryParse(json['last_triggered_at'] as String)
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  bool get isTriggered => status == 'triggered' || status == 'repeated';
  bool get isAcknowledged => status == 'acknowledged';
  bool get isEscalated => status == 'escalated';
}
