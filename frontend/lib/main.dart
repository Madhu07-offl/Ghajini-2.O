import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/router/app_router.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const ProviderScope(
      child: GhajiniApp(),
    ),
  );
}

class GhajiniApp extends StatelessWidget {
  const GhajiniApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Ghajini 2.0',
      theme: AppTheme.elderlyTheme,
      debugShowCheckedModeBanner: false,
      routerConfig: appRouter,
    );
  }
}
