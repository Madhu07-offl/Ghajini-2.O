import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:ghajini_app/core/responsive.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/models/recognition_result.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:ghajini_app/widgets/friendly_error.dart';
import 'package:ghajini_app/widgets/section_card.dart';
import 'package:ghajini_app/widgets/sos_button.dart';
import 'package:ghajini_app/widgets/status_chip.dart';

/// Elderly-friendly, responsive screen for face recognition.
/// Pure web and native compatible (zero dart:io dependencies).
class RecognizeScreen extends ConsumerStatefulWidget {
  const RecognizeScreen({super.key});

  @override
  ConsumerState<RecognizeScreen> createState() => _RecognizeScreenState();
}

class _RecognizeScreenState extends ConsumerState<RecognizeScreen> {
  final ImagePicker _picker = ImagePicker();
  Uint8List? _imageBytes;
  String? _imageName;
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

      final bytes = await file.readAsBytes();

      setState(() {
        _imageBytes = bytes;
        _imageName = file.name;
        _result = null;
        _isLoading = true;
        _errorMessage = null;
      });

      final api = ref.read(apiServiceProvider);
      final tts = ref.read(ttsServiceProvider);

      final res = await api.recognizeFaceBytes(bytes, filename: file.name);

      if (mounted) {
        setState(() {
          _result = res;
          _isLoading = false;
        });

        // Automatically speak result out loud for elderly clarity
        await tts.speak(res.message);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = "I could not process the photo right now. Please try again or ask family.";
        });
        ref.read(ttsServiceProvider).speak(_errorMessage!);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tts = ref.watch(ttsServiceProvider);
    final isWide = Responsive.isWide(context);

    return Scaffold(
      backgroundColor: GhajiniTheme.softCream,
      appBar: AppBar(
        title: const Text(
          'Who Is This?',
          style: TextStyle(
            fontFamily: 'serif',
            fontSize: 26,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: GhajiniTheme.primaryOrange,
        foregroundColor: Colors.white,
        elevation: 2,
        actions: [
          if (isWide)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: CompactSosButton(
                onPressed: () => ref.read(apiServiceProvider).triggerSOSHelp(
                  note: 'SOS triggered from Who Is This screen',
                ),
              ),
            ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: Responsive.screenPadding(context),
          child: ResponsivePatientContainer(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Instruction banner
                SectionCard(
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: GhajiniTheme.softCream,
                          shape: BoxShape.circle,
                          border: Border.all(color: GhajiniTheme.borderLight, width: 2),
                        ),
                        child: const Icon(
                          Icons.face_retouching_natural,
                          size: 36,
                          color: GhajiniTheme.primaryOrange,
                        ),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Text(
                          'Show a photo or take a picture to recognize your loved ones.',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: GhajiniTheme.darkBrown,
                            height: 1.35,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Capture and Gallery Action Buttons
                Row(
                  children: [
                    Expanded(
                      child: BigButton(
                        text: 'Take Photo',
                        icon: Icons.camera_alt,
                        backgroundColor: GhajiniTheme.primaryOrange,
                        textColor: Colors.white,
                        onPressed: _isLoading ? null : () => _pickImage(ImageSource.camera),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: BigButton(
                        text: 'Pick Photo',
                        icon: Icons.photo_library,
                        backgroundColor: Colors.white,
                        textColor: GhajiniTheme.darkBrown,
                        borderColor: GhajiniTheme.primaryOrange,
                        onPressed: _isLoading ? null : () => _pickImage(ImageSource.gallery),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),

                // Loading State
                if (_isLoading)
                  SectionCard(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Column(
                        children: [
                          const CircularProgressIndicator(
                            strokeWidth: 4,
                            valueColor: AlwaysStoppedAnimation<Color>(GhajiniTheme.primaryOrange),
                          ),
                          const SizedBox(height: 20),
                          Text(
                            'Looking into our family memories...',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: GhajiniTheme.darkBrown,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                // Error Banner
                if (_errorMessage != null && !_isLoading) ...[
                  FriendlyError(
                    message: _errorMessage!,
                    onRetry: () => _pickImage(ImageSource.gallery),
                  ),
                  const SizedBox(height: 20),
                ],

                // Selected Photo Preview
                if (_imageBytes != null && !_isLoading) ...[
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: GhajiniTheme.borderLight, width: 3),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x14000000),
                          blurRadius: 10,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(17),
                      child: Image.memory(
                        _imageBytes!,
                        height: 280,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Recognition Result Card
                if (_result != null && !_isLoading)
                  _buildResultCard(context, _result!, tts),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: isWide
          ? null
          : Container(
              padding: const EdgeInsets.all(16),
              color: GhajiniTheme.softCream,
              child: FullWidthSosButton(
                onPressed: () => ref.read(apiServiceProvider).triggerSOSHelp(
                  note: 'SOS triggered from Who Is This screen',
                ),
              ),
            ),
    );
  }

  Widget _buildResultCard(BuildContext context, RecognitionResult res, dynamic tts) {
    Color cardBg;
    Color borderCol;
    StatusType statusType;
    String statusTitle;

    if (res.isMatch) {
      cardBg = GhajiniTheme.successBg;
      borderCol = GhajiniTheme.successGreen;
      statusType = StatusType.success;
      statusTitle = 'Recognized';
    } else if (res.isUncertain) {
      cardBg = const Color(0xFFFFFBEB);
      borderCol = GhajiniTheme.amberAccent;
      statusType = StatusType.warning;
      statusTitle = 'Looks Familiar';
    } else {
      cardBg = const Color(0xFFEFF6FF);
      borderCol = const Color(0xFF2563EB);
      statusType = StatusType.info;
      statusTitle = 'New or Unknown';
    }

    return Card(
      color: cardBg,
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: borderCol, width: 2.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                StatusChip(
                  label: statusTitle,
                  type: statusType,
                  fontSize: 18,
                ),
                const Spacer(),
                IconButton(
                  tooltip: 'Read out loud',
                  icon: const Icon(Icons.volume_up, size: 32, color: GhajiniTheme.darkBrown),
                  onPressed: () => tts.speak(res.message),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Message text
            Text(
              res.message,
              style: const TextStyle(
                fontFamily: 'serif',
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: GhajiniTheme.darkBrown,
                height: 1.35,
              ),
            ),

            if (res.person?.notes != null && res.person!.notes!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: GhajiniTheme.borderLight),
                ),
                child: Text(
                  'Note: ${res.person!.notes}',
                  style: const TextStyle(
                    fontSize: 19,
                    color: GhajiniTheme.darkBrown,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],

            const SizedBox(height: 20),

            // Read aloud button
            BigButton(
              text: 'Speak Again',
              icon: Icons.volume_up,
              backgroundColor: GhajiniTheme.primaryOrange,
              textColor: Colors.white,
              onPressed: () => tts.speak(res.message),
            ),

            // Uncertain Confirmation: "Is this Priya?" with Yes / No
            if (res.isUncertain && res.person != null) ...[
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: GhajiniTheme.amberAccent, width: 2),
                ),
                child: Column(
                  children: [
                    Text(
                      'Is this ${res.person!.name}?',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: GhajiniTheme.darkBrown,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: BigButton(
                            text: 'Yes',
                            icon: Icons.check,
                            backgroundColor: GhajiniTheme.successGreen,
                            textColor: Colors.white,
                            onPressed: () {
                              tts.speak('Great, I have noted this is ${res.person!.name}.');
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Confirmed ${res.person!.name}',
                                    style: const TextStyle(fontSize: 18),
                                  ),
                                  backgroundColor: GhajiniTheme.successGreen,
                                ),
                              );
                            },
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: BigButton(
                            text: 'No',
                            icon: Icons.close,
                            backgroundColor: GhajiniTheme.mutedBrown,
                            textColor: Colors.white,
                            onPressed: () {
                              tts.speak('Understood. I will ask your family.');
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'Noted. We will ask your family.',
                                    style: TextStyle(fontSize: 18),
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],

            // Unknown Person Options
            if (res.isUnknown) ...[
              const SizedBox(height: 16),
              BigButton(
                text: 'Tell Family About Visitor',
                icon: Icons.notifications_active,
                backgroundColor: GhajiniTheme.emergencyRed,
                textColor: Colors.white,
                onPressed: () async {
                  await ref.read(apiServiceProvider).triggerSOSHelp(
                    note: 'Unknown visitor at the door/camera.',
                  );
                  tts.speak('Your family has been told about this visitor.');
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Your family has been notified.', style: TextStyle(fontSize: 18)),
                      backgroundColor: GhajiniTheme.successGreen,
                    ),
                  );
                },
              ),
              const SizedBox(height: 12),
              BigButton(
                text: 'Add to Family & Friends',
                icon: Icons.person_add,
                backgroundColor: Colors.white,
                textColor: GhajiniTheme.darkBrown,
                borderColor: GhajiniTheme.primaryOrange,
                onPressed: () => context.push('/add-person'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
