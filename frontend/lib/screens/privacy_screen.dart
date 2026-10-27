import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/person.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class PrivacyScreen extends ConsumerStatefulWidget {
  const PrivacyScreen({super.key});

  @override
  ConsumerState<PrivacyScreen> createState() => _PrivacyScreenState();
}

class _PrivacyScreenState extends ConsumerState<PrivacyScreen> {
  bool _isExporting = false;
  bool _isWiping = false;

  Future<void> _handleExport() async {
    setState(() => _isExporting = true);
    try {
      final api = ref.read(apiServiceProvider);
      final bytes = await api.exportData();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Data exported successfully (${bytes.length} bytes in ZIP archive).',
            style: const TextStyle(fontSize: 18),
          ),
          backgroundColor: AppTheme.gentleGreen,
          duration: const Duration(seconds: 4),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Could not export data. Please call your family or caregiver.',
            style: TextStyle(fontSize: 18),
          ),
          backgroundColor: AppTheme.distressRed,
        ),
      );
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  Future<void> _handleDeletePerson(Person person) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          'Delete ${person.name}?',
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        content: Text(
          'This will permanently delete ${person.name}\'s profile, saved photos, consent records, and face recognition data.',
          style: const TextStyle(fontSize: 19),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(fontSize: 19)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.distressRed),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete Permanently', style: TextStyle(fontSize: 19, color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final api = ref.read(apiServiceProvider);
        await api.deletePerson(person.id);
        ref.invalidate(peopleListProvider);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${person.name} and face vectors deleted successfully.', style: const TextStyle(fontSize: 18)),
            backgroundColor: AppTheme.gentleGreen,
          ),
        );
      } catch (_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not delete contact. Please call your family.', style: TextStyle(fontSize: 18)),
            backgroundColor: AppTheme.distressRed,
          ),
        );
      }
    }
  }

  Future<void> _handleDeleteEverything() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text(
          'Wipe ALL Personal Data?',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.distressRed),
        ),
        content: const Text(
          'This irreversible GDPR/HIPAA action will permanently delete all memories, faces, reminders, alerts, and recognition indices for this patient.',
          style: TextStyle(fontSize: 19),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(fontSize: 19)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.distressRed),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('WIPE EVERYTHING', style: TextStyle(fontSize: 19, color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => _isWiping = true);
      try {
        final api = ref.read(apiServiceProvider);
        await api.wipeAllData();
        ref.invalidate(peopleListProvider);
        ref.invalidate(upcomingRemindersProvider);
        ref.invalidate(dashboardSummaryProvider);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('All patient personal data wiped clean.', style: TextStyle(fontSize: 18)),
            backgroundColor: AppTheme.gentleGreen,
          ),
        );
        context.go('/');
      } catch (_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not complete wipe. Please try again.', style: TextStyle(fontSize: 18)),
            backgroundColor: AppTheme.distressRed,
          ),
        );
      } finally {
        if (mounted) setState(() => _isWiping = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final peopleAsync = ref.watch(peopleListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Privacy & Data Controls',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // What is stored card
              Card(
                color: Colors.white,
                elevation: 3,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.shield_outlined, color: AppTheme.gentleGreen, size: 30),
                          SizedBox(width: 10),
                          Text(
                            'What Data is Stored?',
                            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      const Text(
                        '1. Facial recognition vectors (512-d embeddings) of consented family & doctors.\n'
                        '2. Personal memory facts (names, addresses, routines).\n'
                        '3. Daily medication reminders & acknowledgment logs.\n'
                        '4. Emergency alert records for caregiver assistance.',
                        style: TextStyle(fontSize: 18, height: 1.5),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Export Data Button
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 68),
                  backgroundColor: const Color(0xFF1E3A8A),
                ),
                onPressed: _isExporting ? null : _handleExport,
                icon: _isExporting
                    ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white))
                    : const Icon(Icons.download_rounded, size: 32),
                label: const Text(
                  'Export My Data (ZIP)',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ),

              const SizedBox(height: 24),

              // Registered Consents & People List
              const Text(
                'Consented People & Faces',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),

              peopleAsync.when(
                data: (people) {
                  if (people.isEmpty) {
                    return const Card(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: Text(
                          'No registered people with consent records found.',
                          style: TextStyle(fontSize: 18),
                        ),
                      ),
                    );
                  }
                  return Column(
                    children: people.map((p) => Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                            leading: CircleAvatar(
                              radius: 26,
                              backgroundColor: AppTheme.accentAmber.withOpacity(0.25),
                              child: Text(
                                p.name.isNotEmpty ? p.name[0] : '?',
                                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                              ),
                            ),
                            title: Text(
                              p.name,
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                            subtitle: Text(
                              '${p.relationship.toUpperCase()} • Explicit Consent Active',
                              style: const TextStyle(fontSize: 16, color: AppTheme.gentleGreen, fontWeight: FontWeight.w600),
                            ),
                            trailing: IconButton(
                              icon: const Icon(Icons.delete_outline, color: AppTheme.distressRed, size: 28),
                              tooltip: 'Delete Person',
                              onPressed: () => _handleDeletePerson(p),
                            ),
                          ),
                        )).toList(),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (_, __) => const Text('Could not load people.', style: TextStyle(fontSize: 18)),
              ),

              const SizedBox(height: 32),

              // Wipe Everything Button
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 72),
                  backgroundColor: AppTheme.distressRed,
                ),
                onPressed: _isWiping ? null : _handleDeleteEverything,
                icon: const Icon(Icons.delete_forever, size: 34),
                label: const Text(
                  'DELETE EVERYTHING',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
