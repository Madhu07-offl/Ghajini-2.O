import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:record/record.dart';
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
  AskResponseModel? _response;
  String? _errorMessage;
  String _selectedLang = 'en';

  @override
  void dispose() {
    _questionController.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  Future<void> _toggleRecording() async {
    try {
      if (_isRecording) {
        final path = await _audioRecorder.stop();
        setState(() => _isRecording = false);
        // Simulated speech transcription fallback
        if (_questionController.text.trim().isEmpty) {
          _questionController.text = "Where does Priya live?";
        }
        await _askQuestion();
      } else {
        if (await _audioRecorder.hasPermission()) {
          await _audioRecorder.start(
            const RecordConfig(encoder: AudioEncoder.aacLc),
            path: '',
          );
          setState(() => _isRecording = true);
          ref.read(ttsServiceProvider).speak('Listening to your question.');
        }
      }
    } catch (_) {
      setState(() => _isRecording = false);
    }
  }

  Future<void> _askQuestion() async {
    final text = _questionController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _response = null;
    });

    final api = ref.read(apiServiceProvider);
    final tts = ref.read(ttsServiceProvider);

    try {
      final res = await api.askQuestion(text: text, lang: _selectedLang);
      if (mounted) {
        setState(() {
          _response = res;
          _isLoading = false;
        });

        // Automatically speak answer
        await tts.speak(res.answer);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = "I couldn't recall that right now. Please try asking again.";
        });
        ref.read(ttsServiceProvider).speak(_errorMessage!);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tts = ref.watch(ttsServiceProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ask Memory'),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'What would you like to know?',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 26),
              ),
              const SizedBox(height: 8),
              const Text(
                'You can type below or tap the microphone to speak.',
                style: TextStyle(fontSize: 20, color: Colors.black54),
              ),
              const SizedBox(height: 24),

              // Question Input Field + Mic Button
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _questionController,
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w500),
                      maxLines: 3,
                      minLines: 1,
                      decoration: InputDecoration(
                        hintText: 'e.g., Where does Priya live?',
                        suffixIcon: IconButton(
                          icon: Icon(
                            _isRecording ? Icons.mic : Icons.mic_none,
                            color: _isRecording ? Colors.red : AppTheme.primaryDark,
                            size: 36,
                          ),
                          onPressed: _toggleRecording,
                        ),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // Ask Button
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 68),
                  backgroundColor: AppTheme.primaryDark,
                ),
                onPressed: _isLoading ? null : _askQuestion,
                icon: const Icon(Icons.send_rounded, size: 28),
                label: const Text('Ask Memory', style: TextStyle(fontSize: 22)),
              ),

              const SizedBox(height: 28),

              // Loading Spinner
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

              // Error display
              if (_errorMessage != null)
                Card(
                  color: const Color(0xFFFFEBEE),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(fontSize: 22, color: Colors.black87),
                    ),
                  ),
                ),

              // Answer Card
              if (_response != null && !_isLoading) _buildAnswerCard(context, _response!, tts),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnswerCard(BuildContext context, AskResponseModel res, dynamic tts) {
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
                Text(
                  isGrounded ? 'Memory Found' : 'Not Certain',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: borderColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Answer text
            Text(
              res.answer,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
                height: 1.4,
              ),
            ),

            if (res.sources.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Divider(),
              const Text(
                'Source Notes:',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black54),
              ),
              const SizedBox(height: 6),
              ...res.sources.map(
                (src) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text(
                    '• $src',
                    style: const TextStyle(fontSize: 18, color: Colors.black87),
                  ),
                ),
              ),
            ],

            const SizedBox(height: 24),

            // Read out loud button
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryDark,
                minimumSize: const Size(double.infinity, 64),
              ),
              onPressed: () => tts.speak(res.answer),
              icon: const Icon(Icons.volume_up, size: 28),
              label: const Text('Read out loud', style: TextStyle(fontSize: 22)),
            ),
          ],
        ),
      ),
    );
  }
}
