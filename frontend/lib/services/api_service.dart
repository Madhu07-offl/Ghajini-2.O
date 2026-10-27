import 'package:dio/dio.dart';
import 'package:ghajini_app/core/api_client.dart';
import 'package:ghajini_app/models/memory.dart';
import 'package:ghajini_app/models/person.dart';
import 'package:ghajini_app/models/recognition_result.dart';
import 'package:ghajini_app/models/reminder.dart';

class ApiService {
  final Dio _dio;

  ApiService({Dio? dio}) : _dio = dio ?? ApiClient.createDio();

  /// Health check
  Future<bool> checkHealth() async {
    try {
      final res = await _dio.get('/health');
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Get registered people
  Future<List<Person>> getPeople({int patientId = 1}) async {
    final res = await _dio.get('/people', queryParameters: {'patient_id': patientId});
    final list = res.data as List<dynamic>;
    return list.map((e) => Person.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Create person (consent is mandatory)
  Future<Person> createPerson({
    required String name,
    required String relationship,
    String? notes,
    required bool consent,
    int patientId = 1,
  }) async {
    final res = await _dio.post(
      '/people',
      data: {
        'name': name,
        'relationship': relationship,
        'notes': notes,
        'consent': consent,
        'patient_id': patientId,
      },
    );
    return Person.fromJson(res.data as Map<String, dynamic>);
  }

  /// Upload face photo for person
  Future<Map<String, dynamic>> uploadPersonFace({
    required int personId,
    required String filePath,
  }) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(filePath),
    });
    final res = await _dio.post('/people/$personId/faces', data: formData);
    return res.data as Map<String, dynamic>;
  }

  /// Delete person
  Future<bool> deletePerson(int personId) async {
    final res = await _dio.delete('/people/$personId');
    return res.statusCode == 200;
  }

  /// Recognize face from photo
  Future<RecognitionResult> recognizeFace(String imagePath) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(imagePath),
    });
    final res = await _dio.post('/recognize', data: formData);
    return RecognitionResult.fromJson(res.data as Map<String, dynamic>);
  }

  /// Ask memory a question
  Future<AskResponseModel> askQuestion({
    required String text,
    String lang = 'en',
    int patientId = 1,
  }) async {
    final res = await _dio.post(
      '/ask',
      data: {
        'text': text,
        'lang': lang,
        'patient_id': patientId,
      },
    );
    return AskResponseModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// Add memory
  Future<Memory> createMemory({
    required String text,
    String category = 'general',
    int patientId = 1,
  }) async {
    final res = await _dio.post(
      '/memories',
      data: {
        'text': text,
        'category': category,
        'patient_id': patientId,
      },
    );
    return Memory.fromJson(res.data as Map<String, dynamic>);
  }

  /// Get upcoming reminders
  Future<List<Reminder>> getUpcomingReminders({int patientId = 1}) async {
    final res = await _dio.get(
      '/reminders/upcoming',
      queryParameters: {'patient_id': patientId},
    );
    final list = res.data as List<dynamic>;
    return list.map((e) => Reminder.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Respond to reminder: "acknowledged" | "snoozed" | "distressed"
  Future<Reminder> respondToReminder({
    required int reminderId,
    required String response,
  }) async {
    final res = await _dio.post(
      '/reminders/$reminderId/respond',
      data: {'response': response},
    );
    return Reminder.fromJson(res.data as Map<String, dynamic>);
  }
}
