import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ghajini_app/models/alert_model.dart';
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

/// Current language selection (en, hi, pa) saved locally in state
final currentLanguageProvider = StateProvider<String>((ref) => 'en');

/// Fetches upcoming reminders
final upcomingRemindersProvider = FutureProvider.autoDispose<List<Reminder>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getUpcomingReminders();
});

/// Fetches currently due reminders (for periodic polling)
final dueRemindersProvider = FutureProvider.autoDispose<List<Reminder>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getDueReminders();
});

/// Fetches recent caregiver alerts
final recentAlertsProvider = FutureProvider.autoDispose<List<AlertModel>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getRecentAlerts();
});

/// Fetches registered people
final peopleListProvider = FutureProvider.autoDispose<List<Person>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getPeople();
});
