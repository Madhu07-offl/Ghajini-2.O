class Memory {
  final int id;
  final int patientId;
  final String text;
  final String? category;
  final DateTime createdAt;

  Memory({
    required this.id,
    required this.patientId,
    required this.text,
    this.category,
    required this.createdAt,
  });

  factory Memory.fromJson(Map<String, dynamic> json) {
    return Memory(
      id: (json['id'] as num).toInt(),
      patientId: ((json['patient_id'] ?? 1) as num).toInt(),
      text: json['text'] as String? ?? '',
      category: json['category'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class AskResponseModel {
  final String answer;
  final bool grounded;
  final List<String> sources;

  AskResponseModel({
    required this.answer,
    required this.grounded,
    required this.sources,
  });

  factory AskResponseModel.fromJson(Map<String, dynamic> json) {
    return AskResponseModel(
      answer: json['answer'] as String? ?? 'I am not sure. Shall I call your family?',
      grounded: json['grounded'] as bool? ?? false,
      sources: (json['sources'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }
}
