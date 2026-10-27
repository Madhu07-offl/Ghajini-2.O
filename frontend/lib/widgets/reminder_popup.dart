import 'package:flutter/material.dart';
import 'package:ghajini_app/core/responsive.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';

class ReminderPopupDialog extends StatelessWidget {
  final Reminder reminder;
  final VoidCallback onDone;
  final VoidCallback onLater;
  final VoidCallback onNeedHelp;

  const ReminderPopupDialog({
    super.key,
    required this.reminder,
    required this.onDone,
    required this.onLater,
    required this.onNeedHelp,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: ResponsivePatientContainer(
        padding: EdgeInsets.zero,
        child: Container(
          decoration: BoxDecoration(
            color: GhajiniTheme.cardWhite,
            borderRadius: BorderRadius.circular(28),
            border: Border.all(
              color: reminder.isCritical ? GhajiniTheme.emergencyRed : GhajiniTheme.primaryOrange,
              width: 3.0,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 28,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Large Icon
              Container(
                width: 90,
                height: 90,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: reminder.isCritical ? GhajiniTheme.emergencyBg : GhajiniTheme.softCream,
                  border: Border.all(
                    color: reminder.isCritical ? GhajiniTheme.emergencyRed : GhajiniTheme.primaryOrange,
                    width: 2.5,
                  ),
                ),
                child: Icon(
                  reminder.isCritical ? Icons.warning_rounded : Icons.notifications_active_rounded,
                  color: reminder.isCritical ? GhajiniTheme.emergencyRed : GhajiniTheme.primaryOrange,
                  size: 52,
                ),
              ),
              const SizedBox(height: 20),

              // Time badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: GhajiniTheme.softCream,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: GhajiniTheme.borderLight),
                ),
                child: Text(
                  "DUE NOW • ${reminder.scheduledTime}",
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: GhajiniTheme.primaryOrange,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Title
              Text(
                reminder.title,
                style: const TextStyle(
                  fontFamily: 'serif',
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: GhajiniTheme.darkBrown,
                  height: 1.3,
                ),
                textAlign: TextAlign.center,
              ),

              if (reminder.message != null && reminder.message!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  reminder.message!,
                  style: const TextStyle(
                    fontSize: 20,
                    color: GhajiniTheme.mutedBrown,
                    height: 1.4,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 32),

              // Button 1: Done
              ElevatedButton.icon(
                onPressed: onDone,
                icon: const Icon(Icons.check_circle_rounded, size: 28, color: Colors.white),
                label: const Text("Done (I Took It)", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  backgroundColor: GhajiniTheme.successGreen,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
              ),
              const SizedBox(height: 14),

              // Button 2: Later (snooze 5 min)
              OutlinedButton.icon(
                onPressed: onLater,
                icon: const Icon(Icons.snooze_rounded, size: 28),
                label: const Text("Later (5 Min)", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  foregroundColor: GhajiniTheme.darkBrown,
                  side: const BorderSide(color: GhajiniTheme.borderLight, width: 2),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
              ),
              const SizedBox(height: 14),

              // Button 3: I need help
              ElevatedButton.icon(
                onPressed: onNeedHelp,
                icon: const Icon(Icons.help_rounded, size: 28, color: Colors.white),
                label: const Text("I Need Help", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  backgroundColor: GhajiniTheme.emergencyRed,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
