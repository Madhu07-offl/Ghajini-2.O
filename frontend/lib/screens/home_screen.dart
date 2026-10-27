import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/constants.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final remindersAsync = ref.watch(upcomingRemindersProvider);
    final tts = ref.watch(ttsServiceProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Ghajini Companion',
          style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
        ),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add_alt_1, size: 30),
            tooltip: 'Caregiver: Add Person',
            onPressed: () => context.push('/add-person'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Warm friendly greeting
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

              const SizedBox(height: 24),

              // Next Reminder Section
              remindersAsync.when(
                data: (reminders) {
                  final active = reminders.where((r) => r.status != 'acknowledged').toList();
                  if (active.isEmpty) {
                    return Card(
                      color: const Color(0xFFE8F5E9),
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Row(
                          children: [
                            const Icon(Icons.check_circle_outline, color: AppTheme.gentleGreen, size: 36),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Text(
                                'All caught up! No pending reminders right now.',
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
                  return _buildReminderBanner(context, ref, nextRem);
                },
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (_, __) => Card(
                  color: const Color(0xFFFFF3CD),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text(
                      'Welcome! Your daily schedule is ready.',
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 32),

              // Action Buttons
              // 1. Who is this?
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 80),
                  backgroundColor: AppTheme.primaryDark,
                ),
                onPressed: () => context.push('/recognize'),
                icon: const Icon(Icons.face_retouching_natural, size: 38),
                label: const Text(
                  'Who is this?',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 20),

              // 2. Ask me
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 80),
                  backgroundColor: const Color(0xFF1E3A8A),
                ),
                onPressed: () => context.push('/ask'),
                icon: const Icon(Icons.question_answer_rounded, size: 38),
                label: const Text(
                  'Ask me anything',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 20),

              // 3. Call family
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 80),
                  backgroundColor: AppTheme.distressRed,
                ),
                onPressed: () => _showCallFamilyDialog(context, tts),
                icon: const Icon(Icons.phone_in_talk, size: 38),
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

  Widget _buildReminderBanner(BuildContext context, WidgetRef ref, Reminder reminder) {
    return Card(
      color: const Color(0xFFFFF9E6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppTheme.accentAmber, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.alarm, color: AppTheme.accentAmber, size: 32),
                const SizedBox(width: 12),
                Text(
                  'Reminder at ${reminder.scheduledTime}',
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF944E00),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              reminder.title,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontSize: 24,
                  ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.gentleGreen,
                      minimumSize: const Size(0, 64),
                    ),
                    onPressed: () async {
                      await ref
                          .read(apiServiceProvider)
                          .respondToReminder(reminderId: reminder.id, response: 'acknowledged');
                      ref.invalidate(upcomingRemindersProvider);
                    },
                    child: const Text('I took it', style: TextStyle(fontSize: 20)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(0, 64),
                      side: const BorderSide(color: Colors.black87, width: 2),
                    ),
                    onPressed: () async {
                      await ref
                          .read(apiServiceProvider)
                          .respondToReminder(reminderId: reminder.id, response: 'snoozed');
                      ref.invalidate(upcomingRemindersProvider);
                    },
                    child: const Text('Later', style: TextStyle(fontSize: 20, color: Colors.black87)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showCallFamilyDialog(BuildContext context, dynamic tts) {
    tts.speak('Calling your daughter Priya and son Arun.');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Calling Family', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
        content: const Text(
          'Connecting to Priya (Daughter) and Arun (Son)... Stay calm, they love you and are here for you.',
          style: TextStyle(fontSize: 22, height: 1.4),
        ),
        actions: [
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.gentleGreen,
              minimumSize: const Size(140, 64),
            ),
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK', style: TextStyle(fontSize: 22)),
          ),
        ],
      ),
    );
  }
}
