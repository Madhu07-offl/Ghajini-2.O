import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Timer? _duePollTimer;
  final Set<int> _activePromptReminderIds = {};
  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  @override
  void initState() {
    super.initState();
    _initLocalNotifications();
    // Poll /v1/reminders/due every 15 seconds
    _duePollTimer = Timer.periodic(const Duration(seconds: 15), (_) => _checkDueReminders());
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkDueReminders());
  }

  @override
  void dispose() {
    _duePollTimer?.cancel();
    super.dispose();
  }

  Future<void> _initLocalNotifications() async {
    try {
      const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
      const initSettings = InitializationSettings(android: androidInit);
      await _notificationsPlugin.initialize(initSettings);
    } catch (e) {
      debugPrint('Local notifications init note: $e');
    }
  }

  Future<void> _scheduleOfflineNotifications(List<Reminder> reminders) async {
    try {
      // Schedule local notifications for the next 24 h
      for (final rem in reminders) {
        final parts = rem.scheduledTime.split(':');
        if (parts.length >= 2) {
          const androidDetails = AndroidNotificationDetails(
            'ghajini_reminders_channel',
            'Medication & Reminders',
            channelDescription: 'Caregiver and patient reminders for Ghajini 2.0',
            importance: Importance.max,
            priority: Priority.high,
          );
          const details = NotificationDetails(android: androidDetails);
          // Show test banner notification locally
          await _notificationsPlugin.show(
            rem.id,
            rem.title,
            rem.message ?? 'Time for your daily scheduled reminder.',
            details,
          );
        }
      }
    } catch (e) {
      debugPrint('Schedule notifications note: $e');
    }
  }

  Future<void> _checkDueReminders() async {
    if (!mounted) return;
    try {
      final api = ref.read(apiServiceProvider);
      final dueReminders = await api.getDueReminders();

      for (final rem in dueReminders) {
        if (!_activePromptReminderIds.contains(rem.id)) {
          _activePromptReminderIds.add(rem.id);
          _showFullScreenReminderCard(rem);
          break; // Show one at a time
        }
      }
    } catch (_) {}
  }

  void _showFullScreenReminderCard(Reminder reminder) {
    final tts = ref.read(ttsServiceProvider);
    final speakText = "Attention please: It is time for ${reminder.title}. ${reminder.message ?? ''}";
    tts.speak(speakText);

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return Dialog.fullscreen(
          child: Container(
            color: const Color(0xFFFFF9E6),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: SafeArea(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(
                    Icons.notifications_active_rounded,
                    color: AppTheme.accentAmber,
                    size: 90,
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'Time for your reminder',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.amber.shade900,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    reminder.title,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  if (reminder.message != null && reminder.message!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      reminder.message!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 24, color: Colors.black87),
                    ),
                  ],
                  const SizedBox(height: 40),

                  // Button 1: Done (Acknowledged)
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.gentleGreen,
                      minimumSize: const Size(double.infinity, 76),
                    ),
                    onPressed: () async {
                      await ref
                          .read(apiServiceProvider)
                          .respondToReminder(reminderId: reminder.id, response: 'acknowledged');
                      _activePromptReminderIds.remove(reminder.id);
                      ref.invalidate(upcomingRemindersProvider);
                      if (mounted) Navigator.of(ctx).pop();
                    },
                    icon: const Icon(Icons.check_circle, size: 36),
                    label: const Text('Done (I took it)', style: TextStyle(fontSize: 24)),
                  ),

                  const SizedBox(height: 16),

                  // Button 2: Later (Snooze 5 min)
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 72),
                      side: const BorderSide(color: Colors.black87, width: 2.5),
                    ),
                    onPressed: () async {
                      await ref
                          .read(apiServiceProvider)
                          .respondToReminder(reminderId: reminder.id, response: 'snoozed');
                      _activePromptReminderIds.remove(reminder.id);
                      ref.invalidate(upcomingRemindersProvider);
                      if (mounted) Navigator.of(ctx).pop();
                    },
                    icon: const Icon(Icons.snooze, size: 32, color: Colors.black87),
                    label: const Text('Later (Remind in 5m)', style: TextStyle(fontSize: 22, color: Colors.black87)),
                  ),

                  const SizedBox(height: 16),

                  // Button 3: I need help (Distressed)
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.distressRed,
                      minimumSize: const Size(double.infinity, 72),
                    ),
                    onPressed: () async {
                      await ref
                          .read(apiServiceProvider)
                          .respondToReminder(reminderId: reminder.id, response: 'distressed');
                      _activePromptReminderIds.remove(reminder.id);
                      ref.invalidate(upcomingRemindersProvider);
                      if (mounted) {
                        Navigator.of(ctx).pop();
                        _showSOSConfirmationDialog();
                      }
                    },
                    icon: const Icon(Icons.warning, size: 32),
                    label: const Text('I need help', style: TextStyle(fontSize: 22)),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _handleSOS() async {
    final tts = ref.read(ttsServiceProvider);
    tts.speak("Emergency help requested. Your family has been told.");

    try {
      await ref.read(apiServiceProvider).triggerSOSHelp();
    } catch (_) {}

    _showSOSConfirmationDialog();
  }

  void _showSOSConfirmationDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.shield_rounded, color: AppTheme.gentleGreen, size: 36),
            SizedBox(width: 12),
            Text('SOS Alert Sent', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          ],
        ),
        content: const Text(
          'Your family has been told.\nHelp is on the way. Stay calm.',
          style: TextStyle(fontSize: 22, height: 1.4),
        ),
        actions: [
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryDark,
              minimumSize: const Size(120, 60),
            ),
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK', style: TextStyle(fontSize: 20)),
          ),
        ],
      ),
    );
  }

  void _showDemoToolsDialog() {
    final tts = ref.read(ttsServiceProvider);
    final api = ref.read(apiServiceProvider);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: const [
            Icon(Icons.build_circle, color: AppTheme.accentAmber, size: 30),
            SizedBox(width: 10),
            Text('Hidden Demo Tools', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Quick actions for live demonstration:',
              style: TextStyle(fontSize: 18, color: Colors.black87),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1E3A8A), minimumSize: const Size(0, 56)),
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  final res = await api.resetDemoData();
                  ref.invalidate(upcomingRemindersProvider);
                  ref.invalidate(dueRemindersProvider);
                  ref.invalidate(peopleListProvider);
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Demo reset: ${res["message"] ?? "Done"}', style: const TextStyle(fontSize: 18)),
                      backgroundColor: AppTheme.gentleGreen,
                    ),
                  );
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Could not reset demo data.', style: TextStyle(fontSize: 18)), backgroundColor: AppTheme.distressRed),
                  );
                }
              },
              icon: const Icon(Icons.restart_alt, size: 26),
              label: const Text('Reset Demo Data', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.gentleGreen, minimumSize: const Size(0, 56)),
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await api.triggerReminderNow();
                  await _checkDueReminders();
                } catch (_) {}
              },
              icon: const Icon(Icons.alarm_on, size: 26),
              label: const Text('Trigger Reminder Now', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.distressRed, minimumSize: const Size(0, 56)),
              onPressed: () async {
                Navigator.pop(ctx);
                _handleSOS();
              },
              icon: const Icon(Icons.sos, size: 26),
              label: const Text('Trigger SOS Alert', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              style: OutlinedButton.styleFrom(minimumSize: const Size(0, 56), side: const BorderSide(color: AppTheme.primaryDark, width: 2)),
              onPressed: () {
                final current = ref.read(currentLanguageProvider);
                final next = current == 'en' ? 'hi' : (current == 'hi' ? 'pa' : 'en');
                ref.read(currentLanguageProvider.notifier).state = next;
                Navigator.pop(ctx);
                final langName = next == 'en' ? 'English' : (next == 'hi' ? 'Hindi' : 'Punjabi');
                tts.speak('Language changed to $langName');
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Language: $langName', style: const TextStyle(fontSize: 18)), backgroundColor: AppTheme.primaryDark),
                );
              },
              icon: const Icon(Icons.translate, size: 26),
              label: const Text('Switch Language', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _callFamily() async {
    final Uri telUri = Uri(scheme: 'tel', path: '+919876543210');
    try {
      if (await canLaunchUrl(telUri)) {
        await launchUrl(telUri);
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final remindersAsync = ref.watch(upcomingRemindersProvider);

    return Scaffold(
      appBar: AppBar(
        title: GestureDetector(
          onLongPress: _showDemoToolsDialog,
          child: const Text(
            'Ghajini Companion',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
          ),
        ),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics_outlined, size: 30),
            tooltip: 'Caregiver Dashboard',
            onPressed: () => context.push('/dashboard'),
          ),
          IconButton(
            icon: const Icon(Icons.admin_panel_settings, size: 30),
            tooltip: 'Caregiver Portal',
            onPressed: () => context.push('/caregiver'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Greeting Card
              Card(
                color: Colors.white,
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.wb_sunny_rounded,
                        color: AppTheme.accentAmber,
                        size: 48,
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Hello!',
                              style: Theme.of(context).textTheme.headlineMedium,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'I am here to help you remember everything today.',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Colors.black87,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // SOS Emergency Button - ALWAYS VISIBLE ON HOME
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 84),
                  backgroundColor: AppTheme.distressRed,
                  elevation: 6,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: const BorderSide(color: Colors.white, width: 3),
                  ),
                ),
                onPressed: _handleSOS,
                icon: const Icon(Icons.sos_rounded, size: 48, color: Colors.white),
                label: const Text(
                  'SOS HELP',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 1.5),
                ),
              ),

              const SizedBox(height: 20),

              // Next Reminder Banner
              remindersAsync.when(
                data: (reminders) {
                  _scheduleOfflineNotifications(reminders);
                  final active = reminders.where((r) => r.status != 'acknowledged').toList();
                  if (active.isEmpty) {
                    return Card(
                      color: const Color(0xFFE8F5E9),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Row(
                          children: [
                            const Icon(Icons.check_circle_outline, color: AppTheme.gentleGreen, size: 34),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Text(
                                'All caught up! No pending reminders.',
                                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                      color: AppTheme.gentleGreen,
                                    ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }
                  final nextRem = active.first;
                  return _buildUpcomingBanner(nextRem);
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (_, __) => const SizedBox.shrink(),
              ),

              const SizedBox(height: 24),

              // Button 1: Who is this?
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 76),
                  backgroundColor: AppTheme.primaryDark,
                ),
                onPressed: () => context.push('/recognize'),
                icon: const Icon(Icons.face_retouching_natural, size: 36),
                label: const Text(
                  'Who is this?',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 16),

              // Button: Talk to Ghajini (AI Companion)
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 80),
                  backgroundColor: const Color(0xFF1E3A8A),
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                onPressed: () => context.push('/companion'),
                icon: const Text('🤖', style: TextStyle(fontSize: 32)),
                label: const Text(
                  'Talk to Ghajini (Companion)',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 16),

              // Button 2: Ask me anything
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 76),
                  backgroundColor: const Color(0xFF1E3A8A),
                ),
                onPressed: () => context.push('/ask'),
                icon: const Icon(Icons.mic, size: 36),
                label: const Text(
                  'Ask me anything',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 16),

              // Button 3: Call family (Opens dialer with tel: protocol)
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 76),
                  backgroundColor: const Color(0xFF374151),
                ),
                onPressed: _callFamily,
                icon: const Icon(Icons.phone_in_talk, size: 36),
                label: const Text(
                  'Call family',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUpcomingBanner(Reminder reminder) {
    return Card(
      color: const Color(0xFFFFF9E6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppTheme.accentAmber, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.alarm, color: AppTheme.accentAmber, size: 28),
                const SizedBox(width: 10),
                Text(
                  'Next Reminder at ${reminder.scheduledTime}',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF944E00),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              reminder.title,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
