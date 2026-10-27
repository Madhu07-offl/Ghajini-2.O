import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/reminder.dart';
import 'package:ghajini_app/widgets/reminder_popup.dart';

void main() {
  group('ReminderPopupDialog Widget Tests', () {
    final testReminder = Reminder(
      id: 1,
      patientId: 1,
      title: 'Take Blood Pressure Tablet',
      message: 'Take one blue tablet with water after eating.',
      scheduledTime: '09:00',
      frequency: 'daily',
      isCritical: true,
      active: true,
    );

    testWidgets('Renders title, message, and time badge properly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: GhajiniTheme.lightTheme,
          home: Scaffold(
            body: ReminderPopupDialog(
              reminder: testReminder,
              onDone: () {},
              onLater: () {},
              onNeedHelp: () {},
            ),
          ),
        ),
      );

      expect(find.text('Take Blood Pressure Tablet'), findsOneWidget);
      expect(find.text('Take one blue tablet with water after eating.'), findsOneWidget);
      expect(find.text('DUE NOW • 09:00'), findsOneWidget);
      expect(find.text('CRITICAL MEDICATION'), findsOneWidget);
    });

    testWidgets('Tapping Done triggers onDone callback', (tester) async {
      bool doneCalled = false;
      await tester.pumpWidget(
        MaterialApp(
          theme: GhajiniTheme.lightTheme,
          home: Scaffold(
            body: ReminderPopupDialog(
              reminder: testReminder,
              onDone: () => doneCalled = true,
              onLater: () {},
              onNeedHelp: () {},
            ),
          ),
        ),
      );

      final doneButtonFinder = find.text('I Have Taken It');
      expect(doneButtonFinder, findsOneWidget);

      await tester.tap(doneButtonFinder);
      await tester.pump();

      expect(doneCalled, isTrue);
    });

    testWidgets('Tapping Later triggers onLater callback', (tester) async {
      bool laterCalled = false;
      await tester.pumpWidget(
        MaterialApp(
          theme: GhajiniTheme.lightTheme,
          home: Scaffold(
            body: ReminderPopupDialog(
              reminder: testReminder,
              onDone: () {},
              onLater: () => laterCalled = true,
              onNeedHelp: () {},
            ),
          ),
        ),
      );

      final laterButtonFinder = find.text('Remind Me In 5 Minutes');
      expect(laterButtonFinder, findsOneWidget);

      await tester.tap(laterButtonFinder);
      await tester.pump();

      expect(laterCalled, isTrue);
    });

    testWidgets('Tapping Need Help triggers onNeedHelp callback', (tester) async {
      bool helpCalled = false;
      await tester.pumpWidget(
        MaterialApp(
          theme: GhajiniTheme.lightTheme,
          home: Scaffold(
            body: ReminderPopupDialog(
              reminder: testReminder,
              onDone: () {},
              onLater: () {},
              onNeedHelp: () => helpCalled = true,
            ),
          ),
        ),
      );

      final helpButtonFinder = find.text('I Need Help / Call Family');
      expect(helpButtonFinder, findsOneWidget);

      await tester.tap(helpButtonFinder);
      await tester.pump();

      expect(helpCalled, isTrue);
    });
  });
}
