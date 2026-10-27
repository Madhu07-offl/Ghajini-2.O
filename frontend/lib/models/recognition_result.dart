import 'package:ghajini_app/models/person.dart';

class RecognitionResult {
  final String status; // "match", "uncertain", "unknown", "no_face"
  final Person? person;
  final double similarity;
  final String message;

  RecognitionResult({
    required this.status,
    this.person,
    required this.similarity,
    required this.message,
  });

  factory RecognitionResult.fromJson(Map<String, dynamic> json) {
    return RecognitionResult(
      status: json['status'] as String? ?? 'unknown',
      person: json['person'] != null
          ? Person.fromJson(json['person'] as Map<String, dynamic>)
          : null,
      similarity: ((json['similarity'] ?? 0.0) as num).toDouble(),
      message: json['message'] as String? ?? '',
    );
  }

  bool get isMatch => status == 'match';
  bool get isUncertain => status == 'uncertain';
  bool get isNoFace => status == 'no_face';
  bool get isUnknown => status == 'unknown';
}
