class Person {
  final int id;
  final int patientId;
  final String name;
  final String relationship;
  final String? notes;
  final DateTime createdAt;
  final int facesCount;

  Person({
    required this.id,
    required this.patientId,
    required this.name,
    required this.relationship,
    this.notes,
    required this.createdAt,
    this.facesCount = 0,
  });

  factory Person.fromJson(Map<String, dynamic> json) {
    return Person(
      id: (json['id'] as num).toInt(),
      patientId: ((json['patient_id'] ?? 1) as num).toInt(),
      name: json['name'] as String? ?? 'Unknown',
      relationship: json['relationship'] as String? ?? 'Family',
      notes: json['notes'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      facesCount: (json['faces_count'] as num?)?.toInt() ?? 0,
    );
  }
}
