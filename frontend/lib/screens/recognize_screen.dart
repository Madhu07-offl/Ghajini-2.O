import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/recognition_result.dart';
import 'package:ghajini_app/providers/app_providers.dart';

class RecognizeScreen extends ConsumerStatefulWidget {
  const RecognizeScreen({super.key});

  @override
  ConsumerState<RecognizeScreen> createState() => _RecognizeScreenState();
}

class _RecognizeScreenState extends ConsumerState<RecognizeScreen> {
  final ImagePicker _picker = ImagePicker();
  String? _selectedImagePath;
  RecognitionResult? _result;
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1200,
      );
      if (file == null) return;

      setState(() {
        _selectedImagePath = file.path;
        _result = null;
        _isLoading = true;
        _errorMessage = null;
      });

      final api = ref.read(apiServiceProvider);
      final tts = ref.read(ttsServiceProvider);

      final res = await api.recognizeFace(file.path);

      if (mounted) {
        setState(() {
          _result = res;
          _isLoading = false;
        });

        // Automatically speak result for elderly accessibility
        await tts.speak(res.message);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = "I could not process the photo right now. Please try again.";
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
        title: const Text('Who Is This?'),
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
                'Point the camera at someone or pick a photo:',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 24),
              ),
              const SizedBox(height: 20),

              // Capture & Pick buttons
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryDark,
                        minimumSize: const Size(0, 72),
                      ),
                      onPressed: _isLoading ? null : () => _pickImage(ImageSource.camera),
                      icon: const Icon(Icons.camera_alt, size: 30),
                      label: const Text('Camera', style: TextStyle(fontSize: 22)),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size(0, 72),
                        side: const BorderSide(color: AppTheme.primaryDark, width: 2.5),
                      ),
                      onPressed: _isLoading ? null : () => _pickImage(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library, size: 30),
                      label: const Text('Gallery', style: TextStyle(fontSize: 22)),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 28),

              // Loading indicator
              if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: Column(
                      children: [
                        CircularProgressIndicator(strokeWidth: 4),
                        SizedBox(height: 20),
                        Text(
                          'Checking my memories...',
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
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: const BorderSide(color: Colors.redAccent, width: 2),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(fontSize: 22, color: Colors.black87),
                    ),
                  ),
                ),

              // Image display and Result Card
              if (_selectedImagePath != null && !_isLoading) ...[
                ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: kIsWeb
                      ? Image.network(_selectedImagePath!, height: 260, fit: BoxFit.cover)
                      : Image.file(File(_selectedImagePath!), height: 260, fit: BoxFit.cover),
                ),
                const SizedBox(height: 24),
              ],

              if (_result != null && !_isLoading) _buildResultCard(context, _result!, tts),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultCard(BuildContext context, RecognitionResult res, dynamic tts) {
    Color cardColor;
    Color borderColor;
    IconData statusIcon;

    if (res.isMatch) {
      cardColor = const Color(0xFFE8F5E9);
      borderColor = AppTheme.gentleGreen;
      statusIcon = Icons.check_circle_rounded;
    } else if (res.isUncertain) {
      cardColor = const Color(0xFFFFF8E1);
      borderColor = AppTheme.accentAmber;
      statusIcon = Icons.help_outline_rounded;
    } else {
      cardColor = const Color(0xFFE3F2FD);
      borderColor = const Color(0xFF1976D2);
      statusIcon = Icons.person_search_rounded;
    }

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
                Icon(statusIcon, color: borderColor, size: 40),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    res.isMatch
                        ? 'Recognized!'
                        : res.isUncertain
                            ? 'Familiar Person'
                            : 'Unknown Face',
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: borderColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Message text
            Text(
              res.message,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
                height: 1.4,
              ),
            ),

            if (res.person?.notes != null && res.person!.notes!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Note: ${res.person!.notes}',
                style: const TextStyle(fontSize: 20, color: Colors.black87, fontStyle: FontStyle.italic),
              ),
            ],

            const SizedBox(height: 24),

            // Action: Speak Again
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryDark,
                minimumSize: const Size(double.infinity, 64),
              ),
              onPressed: () => tts.speak(res.message),
              icon: const Icon(Icons.volume_up, size: 28),
              label: const Text('Read out loud', style: TextStyle(fontSize: 22)),
            ),

            // Uncertain Confirmation: "Is this Priya?" with Yes / No buttons
            if (res.isUncertain && res.person != null) ...[
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.Border.all(color: AppTheme.accentAmber, width: 2),
                ),
                child: Column(
                  children: [
                    Text(
                      'Is this ${res.person!.name}?',
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.gentleGreen,
                              minimumSize: const Size(0, 56),
                            ),
                            onPressed: () {
                              tts.speak('Great, I have confirmed this is ${res.person!.name}.');
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Confirmed ${res.person!.name}', style: const TextStyle(fontSize: 18)),
                                  backgroundColor: AppTheme.gentleGreen,
                                ),
                              );
                            },
                            icon: const Icon(Icons.check, size: 28),
                            label: const Text('Yes', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF6B7280),
                              minimumSize: const Size(0, 56),
                            ),
                            onPressed: () {
                              tts.speak('Understood. I will inform your family.');
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Noted. We will ask your family.', style: TextStyle(fontSize: 18)),
                                ),
                              );
                            },
                            icon: const Icon(Icons.close, size: 28),
                            label: const Text('No', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],

            // Unknown Person: "I do not know this person yet" + Tell Caregiver button
            if (res.isUnknown) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  backgroundColor: AppTheme.distressRed,
                ),
                onPressed: () async {
                  await ref.read(apiServiceProvider).triggerSOSHelp(
                    note: 'Unknown visitor at the door/camera.',
                  );
                  tts.speak('Your family has been told about this visitor.');
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Your family has been notified.', style: TextStyle(fontSize: 18)),
                      backgroundColor: AppTheme.gentleGreen,
                    ),
                  );
                },
                icon: const Icon(Icons.notifications_active, size: 28),
                label: const Text('Tell Caregiver', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 14),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 64),
                  side: const BorderSide(color: AppTheme.primaryDark, width: 2),
                ),
                onPressed: () => context.push('/add-person'),
                icon: const Icon(Icons.person_add, size: 28),
                label: const Text('Add to Family & Friends', style: TextStyle(fontSize: 20)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
