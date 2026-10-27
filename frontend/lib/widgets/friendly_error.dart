import 'package:flutter/material.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:url_launcher/url_launcher.dart';

class FriendlyError extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  final String emergencyPhone;

  const FriendlyError({
    super.key,
    this.message = "I am not sure right now. Shall I call your family?",
    this.onRetry,
    this.emergencyPhone = "+919876543210",
  });

  Future<void> _callFamily(BuildContext context) async {
    final uri = Uri.parse("tel:$emergencyPhone");
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
        return;
      }
    } catch (_) {}

    // Fallback for desktop web / unsupported devices
    if (context.mounted) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(GhajiniTheme.cardRadius),
          ),
          title: const Text("Emergency Contact", style: TextStyle(fontFamily: 'serif', fontWeight: FontWeight.bold)),
          content: Text("Phone: $emergencyPhone\n\nPlease dial this number to reach family.", style: const TextStyle(fontSize: 18)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("OK", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      color: GhajiniTheme.softCream,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(GhajiniTheme.cardRadius),
        side: const BorderSide(color: GhajiniTheme.borderLight, width: 2),
      ),
      margin: const EdgeInsets.all(20),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.help_outline_rounded, color: GhajiniTheme.primaryOrange, size: 54),
            const SizedBox(height: 16),
            Text(
              message,
              style: const TextStyle(
                fontFamily: 'serif',
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: GhajiniTheme.darkBrown,
                height: 1.4,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            BigButton(
              label: "Call Family",
              icon: const Icon(Icons.phone, color: Colors.white, size: 28),
              onPressed: () => _callFamily(context),
              backgroundColor: const Color(0xFF0F172A),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 24),
                label: const Text("Try Again"),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 54),
                  foregroundColor: GhajiniTheme.darkBrown,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
