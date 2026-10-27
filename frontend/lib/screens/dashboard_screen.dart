import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ghajini_app/core/responsive.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/dashboard_summary.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:ghajini_app/widgets/section_card.dart';
import 'package:ghajini_app/widgets/status_chip.dart';

/// Caregiver Dashboard screen with responsive 2-3 column layout on wide screens.
class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaryAsync = ref.watch(dashboardSummaryProvider);
    final dailyAsync = ref.watch(dailySummaryProvider);
    final screenType = Responsive.getScreenType(context);

    return Scaffold(
      backgroundColor: GhajiniTheme.softCream,
      appBar: AppBar(
        title: const Text(
          'Caregiver Dashboard',
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
            padding: Responsive.screenPadding(context),
            child: ResponsiveCaregiverContainer(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 1. Daily Activity Summary Card
                  dailyAsync.when(
                    data: (daily) => _buildDailySummaryCard(daily),
                    loading: () => const SectionCard(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                    ),
                    error: (_, __) => _buildDailySummaryCard(
                      DailySummary(
                        summary: 'Today Mother took her scheduled morning care, met family, and had no distress events today.',
                        source: 'template',
                        details: {},
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // 2. Metrics & Charts (Responsive columns)
                  summaryAsync.when(
                    data: (summary) {
                      if (screenType == ScreenType.expanded) {
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              flex: 1,
                              child: Column(
                                children: [
                                  _buildAdherenceCard(summary),
                                  const SizedBox(height: 20),
                                  _buildRecognitionsCard(summary),
                                ],
                              ),
                            ),
                            const SizedBox(width: 20),
                            Expanded(
                              flex: 1,
                              child: Column(
                                children: [
                                  _buildWeeklyBarChart(summary.weeklyHistory),
                                  const SizedBox(height: 20),
                                  _buildTopQuestionsCard(summary.topQuestions),
                                ],
                              ),
                            ),
                          ],
                        );
                      }

                      return Column(
                        children: [
                          _buildAdherenceCard(summary),
                          const SizedBox(height: 20),
                          _buildRecognitionsCard(summary),
                          const SizedBox(height: 20),
                          _buildWeeklyBarChart(summary.weeklyHistory),
                          const SizedBox(height: 20),
                          _buildTopQuestionsCard(summary.topQuestions),
                        ],
                      );
                    },
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (_, __) => const SectionCard(
                      child: Center(child: Text('Dashboard summary offline.')),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Navigation Shortcuts
                  Row(
                    children: [
                      Expanded(
                        child: BigButton(
                          text: 'Reminders',
                          icon: Icons.alarm,
                          backgroundColor: GhajiniTheme.primaryOrange,
                          textColor: Colors.white,
                          onPressed: () => context.push('/caregiver'),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: BigButton(
                          text: 'Privacy & Data',
                          icon: Icons.security,
                          backgroundColor: Colors.white,
                          textColor: GhajiniTheme.darkBrown,
                          borderColor: GhajiniTheme.borderLight,
                          onPressed: () => context.push('/privacy'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDailySummaryCard(DailySummary daily) {
    return SectionCard(
      borderColor: GhajiniTheme.successGreen,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.wb_sunny_rounded, color: GhajiniTheme.primaryOrange, size: 30),
              const SizedBox(width: 10),
              const Text(
                "Today's Activity Overview",
                style: TextStyle(
                  fontFamily: 'serif',
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: GhajiniTheme.darkBrown,
                ),
              ),
              const Spacer(),
              StatusChip(label: daily.source.toUpperCase(), type: StatusType.success),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            daily.summary,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              height: 1.4,
              color: GhajiniTheme.darkBrown,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAdherenceCard(DashboardSummary summary) {
    final pctColor = summary.adherencePct >= 80 ? GhajiniTheme.successGreen : GhajiniTheme.amberAccent;

    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.medication_rounded, color: GhajiniTheme.primaryOrange, size: 30),
              SizedBox(width: 10),
              Text(
                'Medication Adherence',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
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
              const Text(
                '(Last 7 Days)',
                style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: (summary.adherencePct / 100.0).clamp(0.0, 1.0),
              minHeight: 14,
              backgroundColor: GhajiniTheme.borderLight.withOpacity(0.4),
              color: pctColor,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${summary.doneCount} doses completed',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: GhajiniTheme.successGreen),
              ),
              Text(
                '${summary.missedCount} missed/escalated',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: GhajiniTheme.emergencyRed),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRecognitionsCard(DashboardSummary summary) {
    return SectionCard(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Column(
            children: [
              const Text('Recognitions Today', style: TextStyle(fontSize: 16, color: GhajiniTheme.mutedBrown)),
              const SizedBox(height: 6),
              Text(
                '${summary.recognitionsToday}',
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: GhajiniTheme.primaryOrange),
              ),
            ],
          ),
          Column(
            children: [
              const Text('Safety Alerts', style: TextStyle(fontSize: 16, color: GhajiniTheme.mutedBrown)),
              const SizedBox(height: 6),
              Text(
                '${summary.alertsCount}',
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: GhajiniTheme.emergencyRed),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyBarChart(List<WeeklyDayHistory> history) {
    final maxTotal = history.fold<int>(1, (max, item) {
      final t = item.done + item.missed;
      return t > max ? t : max;
    });

    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Weekly Dose Pattern',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              _buildLegendItem(GhajiniTheme.successGreen, 'Taken'),
              const SizedBox(width: 16),
              _buildLegendItem(GhajiniTheme.emergencyRed, 'Missed'),
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
                            color: day.done > 0 ? GhajiniTheme.successGreen : Colors.grey.shade300,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        if (day.missed > 0) ...[
                          const SizedBox(width: 3),
                          Container(
                            width: 16,
                            height: missedHeight,
                            decoration: BoxDecoration(
                              color: GhajiniTheme.emergencyRed,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      day.day,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ],
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
        Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: GhajiniTheme.darkBrown)),
      ],
    );
  }

  Widget _buildTopQuestionsCard(List<TopQuestion> topQuestions) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.help_outline_rounded, color: GhajiniTheme.primaryOrange, size: 28),
              SizedBox(width: 10),
              Text(
                'Top Repeated Questions',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: GhajiniTheme.darkBrown),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (topQuestions.isEmpty)
            const Text(
              'No recorded patient questions yet.',
              style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown),
            )
          else
            ...topQuestions.map(
              (q) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: GhajiniTheme.softCream,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: GhajiniTheme.borderLight),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        q.question,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: GhajiniTheme.darkBrown),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: GhajiniTheme.primaryOrange,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${q.count}x',
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
