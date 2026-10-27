class AppConstants {
  /// Reads API base URL from --dart-define=API_URL, defaulting to standard localhost/v1
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000/v1',
  );

  static const double minButtonHeight = 64.0;
  static const double minTouchTarget = 64.0;

  static const double titleFontSize = 28.0;
  static const double bodyFontSize = 22.0;
  static const double buttonFontSize = 22.0;
  static const double captionFontSize = 18.0;
}
