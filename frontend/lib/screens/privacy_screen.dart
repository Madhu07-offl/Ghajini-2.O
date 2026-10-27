import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/responsive.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/person.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:ghajini_app/widgets/section_card.dart';

/// Privacy and Data Sovereignty Screen (GDPR / DPDP compliant).
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
            'Data exported successfully (${bytes.length} bytes ZIP archive).',
            style: const TextStyle(fontSize: 18),
          ),
          backgroundColor: GhajiniTheme.successGreen,
          duration: const Duration(seconds: 4),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not export data. Please check connectivity.', style: TextStyle(fontSize: 18)),
          backgroundColor: GhajiniTheme.emergencyRed,
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
        backgroundColor: GhajiniTheme.softCream,
        title: Text(
          'Delete ${person.name}?',
          style: const TextStyle(fontFamily: 'serif', fontSize: 24, fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
        ),
        content: Text(
          'This will permanently delete ${person.name}\'s profile, saved photos, consent records, and face recognition vectors.',
          style: const TextStyle(fontSize: 19, color: GhajiniTheme.darkBrown),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(fontSize: 19, color: GhajiniTheme.mutedBrown)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: GhajiniTheme.emergencyRed),
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
            backgroundColor: GhajiniTheme.successGreen,
          ),
        );
      } catch (_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not delete contact.', style: TextStyle(fontSize: 18)),
            backgroundColor: GhajiniTheme.emergencyRed,
          ),
        );
      }
    }
  }

  Future<void> _handleDeleteEverything() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: GhajiniTheme.softCream,
        title: const Text(
          'Wipe ALL Personal Data?',
          style: TextStyle(fontFamily: 'serif', fontSize: 24, fontWeight: FontWeight.bold, color: GhajiniTheme.emergencyRed),
        ),
        content: const Text(
          'This irreversible action will permanently delete all memories, faces, reminders, alerts, and recognition indices for this patient.',
          style: TextStyle(fontSize: 19, color: GhajiniTheme.darkBrown),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(fontSize: 19, color: GhajiniTheme.mutedBrown)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: GhajiniTheme.emergencyRed),
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
            backgroundColor: GhajiniTheme.successGreen,
          ),
        );
        context.go('/');
      } catch (_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not complete wipe. Please try again.', style: TextStyle(fontSize: 18)),
            backgroundColor: GhajiniTheme.emergencyRed,
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
      backgroundColor: GhajiniTheme.softCream,
      appBar: AppBar(
        title: const Text(
          'Privacy & Data Controls',
          style: TextStyle(
            fontFamily: 'serif',
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: GhajiniTheme.primaryOrange,
        foregroundColor: Colors.white,
        elevation: 2,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: Responsive.screenPadding(context),
          child: ResponsiveCaregiverContainer(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // What is stored card
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.shield_outlined, color: GhajiniTheme.successGreen, size: 30),
                          SizedBox(width: 10),
                          Text(
                            'What Data is Stored?',
                            style: TextStyle(
                              fontFamily: 'serif',
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: GhajiniTheme.darkBrown,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      const Text(
                        '1. Facial recognition vectors (512-d embeddings) of consented family & doctors.\n'
                        '2. Personal memory facts (names, addresses, routines).\n'
                        '3. Daily medication reminders & acknowledgment logs.\n'
                        '4. Voice transcripts are never retained permanently on disk; ephemeral RAM inference only.',
                        style: TextStyle(fontSize: 19, height: 1.5, color: GhajiniTheme.darkBrown),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Data export card
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.download_for_offline_outlined, color: GhajiniTheme.primaryOrange, size: 30),
                          SizedBox(width: 10),
                          Text(
                            'Export Patient Data (Portability)',
                            style: TextStyle(
                              fontFamily: 'serif',
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: GhajiniTheme.darkBrown,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Download all facts, people, reminders, and history as a standard ZIP archive.',
                        style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown),
                      ),
                      const SizedBox(height: 16),
                      BigButton(
                        text: _isExporting ? 'Exporting...' : 'Export All Data (ZIP)',
                        icon: Icons.download_rounded,
                        backgroundColor: GhajiniTheme.primaryOrange,
                        textColor: Colors.white,
                        onPressed: _isExporting ? null : _handleExport,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // People consent & delete list
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Consented People & Faces',
                        style: TextStyle(
                          fontFamily: 'serif',
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: GhajiniTheme.darkBrown,
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Revoke consent and delete individual face recognition profiles below.',
                        style: TextStyle(fontSize: 17, color: GhajiniTheme.mutedBrown),
                      ),
                      const SizedBox(height: 16),
                      peopleAsync.when(
                        data: (people) {
                          if (people.isEmpty) {
                            return const Text('No people registered yet.', style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown));
                          }
                          return ListView.separated(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: people.length,
                            separatorBuilder: (_, __) => const Divider(),
                            itemBuilder: (ctx, i) {
                              final p = people[i];
                              return ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: GhajiniTheme.borderLight,
                                  child: Text(
                                    p.name.isNotEmpty ? p.name[0].toUpperCase() : '?',
                                    style: const TextStyle(fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
                                  ),
                                ),
                                title: Text(p.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                                subtitle: Text('${p.relationship} (Consent active)', style: const TextStyle(fontSize: 16, color: GhajiniTheme.successGreen)),
                                trailing: IconButton(
                                  icon: const Icon(Icons.delete_outline, color: GhajiniTheme.emergencyRed, size: 28),
                                  tooltip: 'Delete and revoke consent',
                                  onPressed: () => _handleDeletePerson(p),
                                ),
                              );
                            },
                          );
                        },
                        loading: () => const Center(child: CircularProgressIndicator()),
                        error: (err, _) => Text('Error: $err'),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // Wipe all data card (GDPR Article 17)
                SectionCard(
                  borderColor: GhajiniTheme.emergencyRed,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.warning_amber_rounded, color: GhajiniTheme.emergencyRed, size: 30),
                          SizedBox(width: 10),
                          Text(
                            'Right to be Forgotten',
                            style: TextStyle(
                              fontFamily: 'serif',
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: GhajiniTheme.emergencyRed,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Permanently wipe all records, enrolled facial embeddings, reminders, and patient memories.',
                        style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown),
                      ),
                      const SizedBox(height: 16),
                      BigButton(
                        text: _isWiping ? 'Wiping...' : 'Wipe All Patient Data',
                        icon: Icons.delete_forever,
                        backgroundColor: GhajiniTheme.emergencyRed,
                        textColor: Colors.white,
                        onPressed: _isWiping ? null : _handleDeleteEverything,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
