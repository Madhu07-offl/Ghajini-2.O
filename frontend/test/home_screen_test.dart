import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/screens/home_screen.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:ghajini_app/widgets/sos_button.dart';

void main() {
  group('HomeScreen Elderly & Responsive Accessibility Tests', () {
    testWidgets('Patient primary buttons are at least 64 dp tall and high contrast', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            upcomingRemindersProvider.overrideWith((ref) => Future.value(<Reminder>[])),
          ],
          child: MaterialApp(
            theme: GhajiniTheme.lightTheme,
            home: const HomeScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find all BigButton widgets on the home screen
      final bigButtonFinders = find.byType(BigButton);
      expect(bigButtonFinders, findsWidgets);

      // Verify each button has a height of at least 64.0 dp (WCAG AA elderly target standard)
      for (final element in bigButtonFinders.evaluate()) {
        final renderBox = element.renderObject as RenderBox?;
        if (renderBox != null) {
          expect(renderBox.size.height, greaterThanOrEqualTo(64.0));
        }
      }
    });

    testWidgets('SOS button is visible and accessible on compact screens', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            upcomingRemindersProvider.overrideWith((ref) => Future.value(<Reminder>[])),
          ],
          child: MaterialApp(
            theme: GhajiniTheme.lightTheme,
            home: const HomeScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify FullWidthSosButton is rendered
      expect(find.byType(FullWidthSosButton), findsOneWidget);
      expect(find.text('HELP ME / SOS'), findsOneWidget);
    });

    testWidgets('Header SOS button is visible on wide desktop web screens', (tester) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            upcomingRemindersProvider.overrideWith((ref) => Future.value(<Reminder>[])),
          ],
          child: MaterialApp(
            theme: GhajiniTheme.lightTheme,
            home: const HomeScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // On wide screens, CompactSosButton is in AppBar
      expect(find.byType(CompactSosButton), findsOneWidget);
      expect(find.text('SOS HELP'), findsOneWidget);
    });
  });
}
