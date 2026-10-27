import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:record/record.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/memory.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class AskScreen extends ConsumerStatefulWidget {
  const AskScreen({super.key});

  @override
  ConsumerState<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends ConsumerState<AskScreen> {
  final TextEditingController _questionController = TextEditingController();
  final AudioRecorder _audioRecorder = AudioRecorder();

  bool _isRecording = false;
  bool _isLoading = false;
  bool _isTranscribing = false;

  String? _transcribedText;
  bool _needsConfirmation = false;

  AskResponseModel? _response;
  String? _errorMessage;

  static const List<Map<String, String>> languages = [
    {'code': 'en', 'name': 'English'},
    {'code': 'hi', 'name': 'हिंदी (Hindi)'},
    {'code': 'pa', 'name': 'ਪੰਜਾਬੀ (Punjabi)'},
  ];

  @override
  void dispose() {
    _questionController.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        setState(() {
          _isRecording = true;
          _errorMessage = null;
          _needsConfirmation = false;
        });

        // Record 16 kHz mono wav as required
        String recordPath = '';
        if (!kIsWeb) {
          final tempDir = Directory.systemTemp;
          recordPath = '${tempDir.path}/ghajini_record_${DateTime.now().millisecondsSinceEpoch}.wav';
        }

        await _audioRecorder.start(
          const RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          ),
          path: recordPath,
        );
      } else {
        setState(() {
          _errorMessage = "Microphone access is needed to listen to you.";
        });
      }
    } catch (e) {
      setState(() {
        _isRecording = false;
        _errorMessage = "Could not start microphone. Please try again or type.";
      });
    }
  }

  Future<void> _stopRecordingAndTranscribe() async {
    try {
      final path = await _audioRecorder.stop();
      setState(() {
        _isRecording = false;
        _isTranscribing = true;
      });

      if (path != null && path.isNotEmpty) {
        final api = ref.read(apiServiceProvider);
        final result = await api.transcribeVoice(path);

        final text = (result['text'] as String?)?.trim() ?? '';
        final needsConf = result['needs_confirmation'] as bool? ?? false;
        final detectedLang = result['language'] as String? ?? 'en';

        // Auto-switch language if detected
        if (languages.any((l) => l['code'] == detectedLang)) {
          ref.read(currentLanguageProvider.notifier).state = detectedLang;
        }

        setState(() {
          _isTranscribing = false;
          _transcribedText = text;
          _questionController.text = text;
          _needsConfirmation = needsConf;
        });

        if (text.isNotEmpty && !needsConf) {
          // High confidence: automatically ask question
          await _askQuestion(text);
        }
      } else {
        setState(() => _isTranscribing = false);
      }
    } catch (e) {
      setState(() {
        _isRecording = false;
        _isTranscribing = false;
        _errorMessage = "I had trouble hearing you. Would you like to try again or ask your family?";
      });
    }
  }

  Future<void> _askQuestion(String query) async {
    final text = query.trim();
    if (text.isEmpty) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _response = null;
      _needsConfirmation = false;
    });

    final currentLang = ref.read(currentLanguageProvider);
    final api = ref.read(apiServiceProvider);
    final tts = ref.read(ttsServiceProvider);

    try {
      final res = await api.askQuestion(text: text, lang: currentLang);
      if (mounted) {
        setState(() {
          _response = res;
          _isLoading = false;
        });

        // Speak answer with mapped locale (en-IN, hi-IN, pa-IN) at rate 0.8
        await tts.speak(res.answer, lang: currentLang);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = "I couldn't recall that right now. Don't worry, your family is always here.";
        });
      }
    }
  }

  Future<void> _callFamily() async {
    final Uri telUri = Uri(scheme: 'tel', path: '+919876543210');
    try {
      if (await canLaunchUrl(telUri)) {
        await launchUrl(telUri);
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final currentLang = ref.watch(currentLanguageProvider);
    final tts = ref.watch(ttsServiceProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ask Memory'),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
        actions: [
          // Language selector
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: currentLang,
                dropdownColor: AppTheme.primaryDark,
                style: const TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold),
                icon: const Icon(Icons.language, color: Colors.white),
                items: languages.map((lang) {
                  return DropdownMenuItem<String>(
                    value: lang['code'],
                    child: Text(lang['name']!),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) {
                    ref.read(currentLanguageProvider.notifier).state = val;
                  }
                },
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'How can I help you today?',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 26),
              ),
              const SizedBox(height: 6),
              const Text(
                'Hold the microphone button to speak, or type below.',
                style: TextStyle(fontSize: 20, color: Colors.black54),
              ),
              const SizedBox(height: 24),

              // Big Push-To-Talk Mic Button
              Center(
                child: GestureDetector(
                  onTapDown: (_) => _startRecording(),
                  onTapUp: (_) => _stopRecordingAndTranscribe(),
                  onTapCancel: () => _stopRecordingAndTranscribe(),
                  child: Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _isRecording ? Colors.redAccent : AppTheme.primaryDark,
                      boxShadow: [
                        BoxShadow(
                          color: (_isRecording ? Colors.redAccent : AppTheme.primaryDark).withOpacity(0.4),
                          blurRadius: 18,
                          spreadRadius: 4,
                        ),
                      ],
                    ),
                    child: Icon(
                      _isRecording ? Icons.mic : Icons.mic_none,
                      color: Colors.white,
                      size: 60,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 12),
              Center(
                child: Text(
                  _isRecording
                      ? 'Listening... Release to ask'
                      : _isTranscribing
                          ? 'Transcribing your voice...'
                          : 'Hold button to speak',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: _isRecording ? Colors.redAccent : Colors.black87,
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Needs Confirmation Prompt ("Did you ask: ...?")
              if (_needsConfirmation && _transcribedText != null && _transcribedText!.isNotEmpty)
                Card(
                  color: const Color(0xFFFFF8E1),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: const BorderSide(color: AppTheme.accentAmber, width: 2.5),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.hearing, color: AppTheme.accentAmber, size: 32),
                            SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'Just to make sure I heard you right:',
                                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Did you ask: "$_transcribedText"?',
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.gentleGreen,
                                  minimumSize: const Size(0, 64),
                                ),
                                onPressed: () => _askQuestion(_transcribedText!),
                                child: const Text('Yes, ask this', style: TextStyle(fontSize: 20)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: OutlinedButton(
                                style: OutlinedButton.styleFrom(
                                  minimumSize: const Size(0, 64),
                                  side: const BorderSide(color: Colors.black54, width: 2),
                                ),
                                onPressed: () {
                                  setState(() {
                                    _needsConfirmation = false;
                                    _transcribedText = null;
                                    _questionController.clear();
                                  });
                                },
                                child: const Text('No, try again', style: TextStyle(fontSize: 20, color: Colors.black87)),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

              const SizedBox(height: 16),

              // Text Question Field
              TextField(
                controller: _questionController,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w500),
                maxLines: 2,
                decoration: InputDecoration(
                  hintText: 'e.g., Where does Priya live?',
                  suffixIcon: IconButton(
                    icon: const Icon(Icons.send, color: AppTheme.primaryDark, size: 30),
                    onPressed: _isLoading ? null : () => _askQuestion(_questionController.text),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  backgroundColor: AppTheme.primaryDark,
                ),
                onPressed: _isLoading ? null : () => _askQuestion(_questionController.text),
                icon: const Icon(Icons.search, size: 28),
                label: const Text('Ask Ghajini', style: TextStyle(fontSize: 22)),
              ),

              const SizedBox(height: 24),

              if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Column(
                      children: [
                        CircularProgressIndicator(strokeWidth: 4),
                        SizedBox(height: 16),
                        Text(
                          'Searching your memories...',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ),

              // Friendly Error Card with Call Family Option
              if (_errorMessage != null)
                Card(
                  color: const Color(0xFFFFEBEE),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: const BorderSide(color: Colors.redAccent, width: 2),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          _errorMessage!,
                          style: const TextStyle(fontSize: 22, color: Colors.black87),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.distressRed,
                            minimumSize: const Size(double.infinity, 60),
                          ),
                          onPressed: _callFamily,
                          icon: const Icon(Icons.phone),
                          label: const Text('Call Family Now', style: TextStyle(fontSize: 20)),
                        ),
                      ],
                    ),
                  ),
                ),

              // Answer Display Card with Replay Button
              if (_response != null && !_isLoading) _buildAnswerCard(context, _response!, tts, currentLang),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnswerCard(BuildContext context, AskResponseModel res, dynamic tts, String lang) {
    final isGrounded = res.grounded;
    final cardColor = isGrounded ? const Color(0xFFE8F5E9) : const Color(0xFFFFF3E0);
    final borderColor = isGrounded ? AppTheme.gentleGreen : AppTheme.accentAmber;

    return Card(
      color: cardColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: BorderSide(color: borderColor, width: 3),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(
                  isGrounded ? Icons.lightbulb_outline : Icons.help_outline,
                  color: borderColor,
                  size: 36,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    isGrounded ? 'Memory Answer' : 'Not Certain',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: borderColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              res.answer,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 24),

            // Replay Button
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryDark,
                minimumSize: const Size(double.infinity, 64),
              ),
              onPressed: () => tts.speak(res.answer, lang: lang),
              icon: const Icon(Icons.replay, size: 28),
              label: const Text('Replay Speech', style: TextStyle(fontSize: 22)),
            ),

            if (!isGrounded) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.distressRed,
                  minimumSize: const Size(double.infinity, 64),
                ),
                onPressed: _callFamily,
                icon: const Icon(Icons.phone),
                label: const Text('Call Family', style: TextStyle(fontSize: 22)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
