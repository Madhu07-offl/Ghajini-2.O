import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class CaregiverScreen extends ConsumerStatefulWidget {
  const CaregiverScreen({super.key});

  @override
  ConsumerState<CaregiverScreen> createState() => _CaregiverScreenState();
}

class _CaregiverScreenState extends ConsumerState<CaregiverScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _showAddEditReminderDialog([Reminder? existing]) {
    final titleController = TextEditingController(text: existing?.title ?? '');
    final messageController = TextEditingController(text: existing?.message ?? '');
    final timeController = TextEditingController(text: existing?.scheduledTime ?? '09:00');
    bool isCritical = existing?.isCritical ?? false;
    String repeatOption = existing?.rrule?.contains('WEEKLY') == true ? 'weekly' : 'daily';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(
            existing == null ? 'Create Reminder' : 'Edit Reminder',
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleController,
                  style: const TextStyle(fontSize: 20),
                  decoration: const InputDecoration(labelText: 'Title *', hintText: 'e.g., Blood Pressure Pill'),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: messageController,
                  style: const TextStyle(fontSize: 18),
                  decoration: const InputDecoration(labelText: 'Instructions', hintText: 'e.g., Take with full glass of water'),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: timeController,
                  style: const TextStyle(fontSize: 20),
                  decoration: const InputDecoration(labelText: 'Time (HH:MM) *', hintText: '09:00'),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  value: repeatOption,
                  decoration: const InputDecoration(labelText: 'Repeat'),
                  items: const [
                    DropdownMenuItem(value: 'daily', child: Text('Daily (Every Day)', style: TextStyle(fontSize: 18))),
                    DropdownMenuItem(value: 'weekly', child: Text('Weekly', style: TextStyle(fontSize: 18))),
                  ],
                  onChanged: (val) {
                    if (val != null) setDialogState(() => repeatOption = val);
                  },
                ),
                const SizedBox(height: 14),
                CheckboxListTile(
                  value: isCritical,
                  title: const Text('Critical Medication', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  subtitle: const Text('Fires even during quiet hours (10PM-6AM)'),
                  onChanged: (val) => setDialogState(() => isCritical = val ?? false),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Cancel', style: TextStyle(fontSize: 18)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryDark),
              onPressed: () async {
                final api = ref.read(apiServiceProvider);
                final rrule = repeatOption == 'weekly' ? 'FREQ=WEEKLY' : 'FREQ=DAILY';

                if (existing == null) {
                  await api.createReminder(
                    title: titleController.text.trim(),
                    message: messageController.text.trim().isNotEmpty ? messageController.text.trim() : null,
                    scheduledTime: timeController.text.trim(),
                    frequency: repeatOption,
                    rrule: rrule,
                    isCritical: isCritical,
                  );
                } else {
                  await api.updateReminder(
                    existing.id,
                    title: titleController.text.trim(),
                    message: messageController.text.trim().isNotEmpty ? messageController.text.trim() : null,
                    scheduledTime: timeController.text.trim(),
                    frequency: repeatOption,
                    rrule: rrule,
                    isCritical: isCritical,
                  );
                }

                ref.invalidate(upcomingRemindersProvider);
                if (mounted) Navigator.of(ctx).pop();
              },
              child: const Text('Save', style: TextStyle(fontSize: 18)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final remindersAsync = ref.watch(upcomingRemindersProvider);
    final alertsAsync = ref.watch(recentAlertsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Caregiver Portal'),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics_outlined, size: 28),
            tooltip: 'Adherence Analytics',
            onPressed: () => context.push('/dashboard'),
          ),
          IconButton(
            icon: const Icon(Icons.privacy_tip_outlined, size: 28),
            tooltip: 'Privacy & Data',
            onPressed: () => context.push('/privacy'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          labelStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          tabs: const [
            Tab(text: 'Reminders'),
            Tab(text: 'Alerts'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add, size: 28),
            tooltip: 'Add Contact',
            onPressed: () => context.push('/add-person'),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Reminders Management
          remindersAsync.when(
            data: (reminders) => Scaffold(
              floatingActionButton: FloatingActionButton.extended(
                backgroundColor: AppTheme.primaryDark,
                onPressed: () => _showAddEditReminderDialog(),
                icon: const Icon(Icons.add, color: Colors.white),
                label: const Text('New Reminder', style: TextStyle(color: Colors.white, fontSize: 18)),
              ),
              body: reminders.isEmpty
                  ? const Center(
                      child: Text('No reminders configured yet.', style: TextStyle(fontSize: 20, color: Colors.black54)),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: reminders.length,
                      itemBuilder: (ctx, i) {
                        final rem = reminders[i];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: ListTile(
                            leading: Icon(
                              rem.isCritical ? Icons.emergency : Icons.alarm,
                              color: rem.isCritical ? Colors.red : AppTheme.primaryDark,
                              size: 34,
                            ),
                            title: Text(rem.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                            subtitle: Text(
                              'Time: ${rem.scheduledTime} | Repeat: ${rem.frequency}${rem.isCritical ? " | Critical" : ""}',
                              style: const TextStyle(fontSize: 16),
                            ),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.edit, color: Colors.blue),
                                  onPressed: () => _showAddEditReminderDialog(rem),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.delete, color: Colors.red),
                                  onPressed: () async {
                                    await ref.read(apiServiceProvider).deleteReminder(rem.id);
                                    ref.invalidate(upcomingRemindersProvider);
                                  },
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error loading reminders: $e')),
          ),

          // Tab 2: Recent Alerts View
          alertsAsync.when(
            data: (alerts) => alerts.isEmpty
                ? const Center(
                    child: Text('No alerts triggered yet.', style: TextStyle(fontSize: 20, color: Colors.black54)),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: alerts.length,
                    itemBuilder: (ctx, i) {
                      final alert = alerts[i];
                      final isEmergency = alert.alertType.contains('emergency') || alert.alertType.contains('sos');
                      return Card(
                        color: isEmergency ? const Color(0xFFFFEBEE) : const Color(0xFFFFF8E1),
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: Icon(
                            isEmergency ? Icons.warning_amber_rounded : Icons.notification_important,
                            color: isEmergency ? Colors.red : Colors.orange,
                            size: 36,
                          ),
                          title: Text(alert.alertType.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          subtitle: Text(alert.message, style: const TextStyle(fontSize: 18, color: Colors.black87)),
                          trailing: Text(
                            alert.status,
                            style: TextStyle(fontWeight: FontWeight.bold, color: isEmergency ? Colors.red : Colors.orange),
                          ),
                        ),
                      );
                    },
                  ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error loading alerts: $e')),
          ),
        ],
      ),
    );
  }
}
