import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  final FlutterTts _flutterTts = FlutterTts();
  bool _initialized = false;

  static const Map<String, String> langLocaleMap = {
    'en': 'en-IN',
    'hi': 'hi-IN',
    'pa': 'pa-IN',
  };

  Future<void> init() async {
    if (_initialized) return;
    try {
      // Speech rate 0.8 as specified in Phase 2 requirements
      await _flutterTts.setSpeechRate(0.8);
      await _flutterTts.setVolume(1.0);
      await _flutterTts.setPitch(1.0);
      _initialized = true;
    } catch (e) {
      debugPrint('TTS init note: $e');
    }
  }

  Future<void> speak(String text, {String lang = 'en'}) async {
    if (text.isEmpty) return;
    try {
      await init();
      final locale = langLocaleMap[lang.toLowerCase().substring(0, 2)] ?? 'en-IN';

      // Check if locale voice is supported; if not, do not crash
      final isAvailable = await _flutterTts.isLanguageAvailable(locale);
      if (isAvailable == true) {
        await _flutterTts.setLanguage(locale);
      } else {
        // Fallback to en-IN or skip speech
        await _flutterTts.setLanguage('en-IN');
      }

      await _flutterTts.stop();
      await _flutterTts.speak(text);
    } catch (e) {
      // Gracefully show text only, do not crash if locale voice is missing
      debugPrint('TTS voice missing or unsupported for locale: $e');
    }
  }

  Future<void> stop() async {
    try {
      await _flutterTts.stop();
    } catch (_) {}
  }
}
