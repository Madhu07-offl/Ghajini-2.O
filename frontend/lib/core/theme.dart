import 'package:flutter/material.dart';
import 'package:ghajini_app/core/constants.dart';

class AppTheme {
  // High contrast palette tailored for elderly vision
  static const Color primaryDark = Color(0xFF0F2942);
  static const Color accentAmber = Color(0xFFE67E22);
  static const Color softBackground = Color(0xFFF9FAF8);
  static const Color cardBackground = Color(0xFFFFFFFF);
  static const Color highContrastText = Color(0xFF111827);
  static const Color gentleGreen = Color(0xFF1B8A5A);
  static const Color distressRed = Color(0xFFC0392B);

  static ThemeData get elderlyTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryDark,
        primary: primaryDark,
        secondary: accentAmber,
        background: softBackground,
        surface: cardBackground,
      ),
      scaffoldBackgroundColor: softBackground,

      // High contrast, large typography (20 sp+)
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 32.0,
          fontWeight: FontWeight.bold,
          color: highContrastText,
          height: 1.3,
        ),
        headlineMedium: TextStyle(
          fontSize: AppConstants.titleFontSize,
          fontWeight: FontWeight.bold,
          color: highContrastText,
          height: 1.3,
        ),
        bodyLarge: TextStyle(
          fontSize: AppConstants.bodyFontSize,
          fontWeight: FontWeight.w600,
          color: highContrastText,
          height: 1.4,
        ),
        bodyMedium: TextStyle(
          fontSize: 20.0,
          fontWeight: FontWeight.normal,
          color: highContrastText,
          height: 1.4,
        ),
        labelLarge: TextStyle(
          fontSize: AppConstants.buttonFontSize,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),

      // Buttons with minimum height of 64 dp
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, AppConstants.minButtonHeight),
          backgroundColor: primaryDark,
          foregroundColor: Colors.white,
          elevation: 4.0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16.0),
          ),
          textStyle: const TextStyle(
            fontSize: AppConstants.buttonFontSize,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(double.infinity, AppConstants.minButtonHeight),
          foregroundColor: primaryDark,
          side: const BorderSide(color: primaryDark, width: 2.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16.0),
          ),
          textStyle: const TextStyle(
            fontSize: AppConstants.buttonFontSize,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardBackground,
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 22),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16.0),
          borderSide: const BorderSide(color: primaryDark, width: 2.0),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16.0),
          borderSide: const BorderSide(color: Colors.grey, width: 2.0),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16.0),
          borderSide: const BorderSide(color: primaryDark, width: 3.0),
        ),
        labelStyle: const TextStyle(fontSize: 20.0, color: Colors.black87),
        hintStyle: const TextStyle(fontSize: 20.0, color: Colors.black54),
      ),

      cardTheme: CardTheme(
        color: cardBackground,
        elevation: 4.0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20.0),
          side: const BorderSide(color: Color(0xFFE5E7EB), width: 1.5),
        ),
      ),
    );
  }
}
