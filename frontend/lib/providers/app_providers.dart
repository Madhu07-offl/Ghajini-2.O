import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ghajini_app/models/person.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/services/api_service.dart';
import 'package:ghajini_app/services/tts_service.dart';

final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

final ttsServiceProvider = Provider<TtsService>((ref) {
  return TtsService();
});

/// Fetches upcoming reminders
final upcomingRemindersProvider = FutureProvider.autoDispose<List<Reminder>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getUpcomingReminders();
});

/// Fetches registered people
final peopleListProvider = FutureProvider.autoDispose<List<Person>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getPeople();
});
