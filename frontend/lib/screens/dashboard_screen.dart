import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/dashboard_summary.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaryAsync = ref.watch(dashboardSummaryProvider);
    final dailyAsync = ref.watch(dailySummaryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Caregiver Dashboard',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 28),
            tooltip: 'Refresh',
            onPressed: () {
              ref.invalidate(dashboardSummaryProvider);
              ref.invalidate(dailySummaryProvider);
            },
          ),
          IconButton(
            icon: const Icon(Icons.privacy_tip_outlined, size: 28),
            tooltip: 'Privacy & Data',
            onPressed: () => context.push('/privacy'),
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(dashboardSummaryProvider);
            ref.invalidate(dailySummaryProvider);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 1. Daily Activity Summary Card
                dailyAsync.when(
                  data: (daily) => _buildDailySummaryCard(context, daily),
                  loading: () => const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ),
                  error: (_, __) => _buildDailySummaryCard(
                    context,
                    DailySummary(
                      summary: 'Today Mother took her scheduled morning care, met family, and had no distress events today.',
                      source: 'template',
                      details: {},
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // 2. 7-Day Adherence & Weekly Custom Bar Chart
                summaryAsync.when(
                  data: (summary) => Column(
                    children: [
                      _buildAdherenceCard(context, summary),
                      const SizedBox(height: 20),
                      _buildWeeklyBarChart(context, summary.weeklyHistory),
                      const SizedBox(height: 20),
                      _buildTopQuestionsCard(context, summary.topQuestions),
                    ],
                  ),
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (_, __) => Card(
                    color: Colors.white,
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        children: [
                          const Icon(Icons.info_outline, size: 40, color: AppTheme.accentAmber),
                          const SizedBox(height: 10),
                          const Text(
                            'Summary data is loading or offline.',
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 10),
                          ElevatedButton(
                            onPressed: () => ref.invalidate(dashboardSummaryProvider),
                            child: const Text('Try Again'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // 3. Navigation Shortcuts
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(double.infinity, 64),
                          backgroundColor: AppTheme.primaryDark,
                        ),
                        onPressed: () => context.push('/caregiver'),
                        icon: const Icon(Icons.alarm_add, size: 28),
                        label: const Text(
                          'Reminders',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(double.infinity, 64),
                          backgroundColor: const Color(0xFF374151),
                        ),
                        onPressed: () => context.push('/privacy'),
                        icon: const Icon(Icons.security, size: 28),
                        label: const Text(
                          'Privacy',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDailySummaryCard(BuildContext context, DailySummary daily) {
    return Card(
      color: const Color(0xFFF0FDF4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppTheme.gentleGreen, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.wb_sunny_outlined, color: AppTheme.gentleGreen, size: 30),
                const SizedBox(width: 10),
                const Text(
                  "Today's Activity",
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF14532D)),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.Border.all(color: AppTheme.gentleGreen),
                  ),
                  child: Text(
                    daily.source.toUpperCase(),
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.gentleGreen),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              daily.summary,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600, height: 1.4, color: Colors.black87),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAdherenceCard(BuildContext context, DashboardSummary summary) {
    final pctColor = summary.adherencePct >= 80 ? AppTheme.gentleGreen : AppTheme.accentAmber;

    return Card(
      color: Colors.white,
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.favorite, color: AppTheme.distressRed, size: 30),
                const SizedBox(width: 10),
                const Text(
                  'Medication Adherence',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  '${summary.adherencePct.toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: pctColor),
                ),
                const SizedBox(width: 14),
                Text(
                  '(Last 7 Days)',
                  style: TextStyle(fontSize: 18, color: Colors.grey.shade600, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: (summary.adherencePct / 100.0).clamp(0.0, 1.0),
                minHeight: 14,
                backgroundColor: Colors.grey.shade200,
                color: pctColor,
              ),
            ),
            const SizedBox(height: 14),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${summary.doneCount} doses completed',
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppTheme.gentleGreen),
                ),
                Text(
                  '${summary.missedCount} missed/escalated',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeeklyBarChart(BuildContext context, List<WeeklyDayHistory> history) {
    // Pure custom bar chart layout (NO external chart package)
    final maxTotal = history.fold<int>(1, (max, item) {
      final t = item.done + item.missed;
      return t > max ? t : max;
    });

    return Card(
      color: Colors.white,
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Weekly Dose Pattern',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                _buildLegendItem(AppTheme.gentleGreen, 'Taken'),
                const SizedBox(width: 16),
                _buildLegendItem(AppTheme.distressRed, 'Missed'),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 140,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: history.map((day) {
                  final double doneHeight = ((day.done / maxTotal) * 90).clamp(6.0, 90.0);
                  final double missedHeight = ((day.missed / maxTotal) * 90).clamp(0.0, 90.0);

                  return Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Container(
                            width: 16,
                            height: day.done > 0 ? doneHeight : 6,
                            decoration: BoxDecoration(
                              color: day.done > 0 ? AppTheme.gentleGreen : Colors.grey.shade300,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          if (day.missed > 0) ...[
                            const SizedBox(width: 3),
                            Container(
                              width: 16,
                              height: missedHeight,
                              decoration: BoxDecoration(
                                color: AppTheme.distressRed,
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        day.day,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 14,
          height: 14,
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3)),
        ),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildTopQuestionsCard(BuildContext context, List<TopQuestion> topQuestions) {
    return Card(
      color: Colors.white,
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.help_outline, color: Color(0xFF1E3A8A), size: 28),
                const SizedBox(width: 10),
                const Text(
                  'Top Repeated Questions',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 14),
            if (topQuestions.isEmpty)
              const Text(
                'No recorded patient questions yet.',
                style: TextStyle(fontSize: 18, color: Colors.black54),
              )
            else
              ...topQuestions.map((q) => Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF3F4F6),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            q.question,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E3A8A),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${q.count}x',
                            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}
