import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:ghajini_app/core/responsive.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/widgets/big_button.dart';
import 'package:ghajini_app/widgets/section_card.dart';

/// Elderly/caregiver-friendly screen to add a family member or friend.
/// Fully web and native compatible (zero dart:io dependencies).
class AddPersonScreen extends ConsumerStatefulWidget {
  const AddPersonScreen({super.key});

  @override
  ConsumerState<AddPersonScreen> createState() => _AddPersonScreenState();
}

class _AddPersonScreenState extends ConsumerState<AddPersonScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _relationshipController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  bool _consentGiven = false;
  Uint8List? _photoBytes;
  String? _photoFileName;
  bool _isSubmitting = false;
  String? _errorMessage;
  String? _successMessage;

  final ImagePicker _picker = ImagePicker();

  @override
  void dispose() {
    _nameController.dispose();
    _relationshipController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1000,
      );
      if (file != null) {
        final bytes = await file.readAsBytes();
        setState(() {
          _photoBytes = bytes;
          _photoFileName = file.name;
        });
      }
    } catch (_) {}
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (!_consentGiven) {
      setState(() {
        _errorMessage = "Consent is required to store this person's details.";
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
      _successMessage = null;
    });

    final api = ref.read(apiServiceProvider);
    final tts = ref.read(ttsServiceProvider);

    try {
      final person = await api.createPerson(
        name: _nameController.text.trim(),
        relationship: _relationshipController.text.trim(),
        notes: _notesController.text.trim().isNotEmpty ? _notesController.text.trim() : null,
        consent: true,
      );

      // Upload face photo if provided (byte-based for cross-platform web & native)
      if (_photoBytes != null) {
        await api.uploadPersonFaceBytes(
          personId: person.id,
          bytes: _photoBytes!,
          filename: _photoFileName ?? 'face_${person.id}.jpg',
        );
      }

      ref.invalidate(peopleListProvider);

      setState(() {
        _isSubmitting = false;
        _successMessage = "Successfully registered ${person.name}!";
      });

      await tts.speak("${person.name} has been added to family and friends.");

      await Future.delayed(const Duration(seconds: 2));
      if (mounted) {
        context.pop();
      }
    } catch (e) {
      setState(() {
        _isSubmitting = false;
        _errorMessage = "Could not register person. Please verify connection and try again.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GhajiniTheme.softCream,
      appBar: AppBar(
        title: const Text(
          'Add Family or Friend',
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
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: Responsive.screenPadding(context),
          child: ResponsiveCaregiverContainer(
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header Card
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Caregiver Portal: Add Contact',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            color: GhajiniTheme.darkBrown,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Enter their details and photo so Ghajini can recognize and introduce them.',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: GhajiniTheme.mutedBrown,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Contact Form Fields Card
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        TextFormField(
                          controller: _nameController,
                          style: const TextStyle(fontSize: 22, color: GhajiniTheme.darkBrown),
                          decoration: const InputDecoration(
                            labelText: 'Full Name *',
                            hintText: 'e.g., Priya or Dr. Sharma',
                            prefixIcon: Icon(Icons.person, color: GhajiniTheme.primaryOrange),
                          ),
                          validator: (val) =>
                              val == null || val.trim().isEmpty ? 'Please enter a name' : null,
                        ),
                        const SizedBox(height: 20),

                        TextFormField(
                          controller: _relationshipController,
                          style: const TextStyle(fontSize: 22, color: GhajiniTheme.darkBrown),
                          decoration: const InputDecoration(
                            labelText: 'Relationship *',
                            hintText: 'e.g., Daughter, Son, Neurologist',
                            prefixIcon: Icon(Icons.favorite_rounded, color: GhajiniTheme.primaryOrange),
                          ),
                          validator: (val) =>
                              val == null || val.trim().isEmpty ? 'Please enter relationship' : null,
                        ),
                        const SizedBox(height: 20),

                        TextFormField(
                          controller: _notesController,
                          style: const TextStyle(fontSize: 20, color: GhajiniTheme.darkBrown),
                          maxLines: 2,
                          decoration: const InputDecoration(
                            labelText: 'Helpful Memory Notes (optional)',
                            hintText: 'e.g., Lives in Bangalore, visits every Sunday with sweet mangoes',
                            prefixIcon: Icon(Icons.note_alt_rounded, color: GhajiniTheme.primaryOrange),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Photo Attachment Card
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Face Photo for Recognition',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: GhajiniTheme.darkBrown,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Take a clear, well-lit photo of their face looking directly at the camera.',
                          style: TextStyle(fontSize: 18, color: GhajiniTheme.mutedBrown),
                        ),
                        const SizedBox(height: 16),

                        if (_photoBytes != null) ...[
                          Center(
                            child: Container(
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: GhajiniTheme.borderLight, width: 2),
                              ),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(14),
                                child: Image.memory(
                                  _photoBytes!,
                                  height: 200,
                                  width: 200,
                                  fit: BoxFit.cover,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],

                        Row(
                          children: [
                            Expanded(
                              child: BigButton(
                                text: 'Camera',
                                icon: Icons.camera_alt,
                                backgroundColor: GhajiniTheme.primaryOrange,
                                textColor: Colors.white,
                                onPressed: () => _pickPhoto(ImageSource.camera),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: BigButton(
                                text: 'Gallery',
                                icon: Icons.photo_library,
                                backgroundColor: Colors.white,
                                textColor: GhajiniTheme.darkBrown,
                                borderColor: GhajiniTheme.primaryOrange,
                                onPressed: () => _pickPhoto(ImageSource.gallery),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Mandatory Consent Checkbox Card
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: _consentGiven ? GhajiniTheme.successGreen : GhajiniTheme.borderLight,
                        width: 2,
                      ),
                    ),
                    child: CheckboxListTile(
                      value: _consentGiven,
                      onChanged: (val) => setState(() => _consentGiven = val ?? false),
                      title: const Text(
                        'I confirm consent has been provided to store this person\'s name and facial features for patient assistance.',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: GhajiniTheme.darkBrown,
                        ),
                      ),
                      controlAffinity: ListTileControlAffinity.leading,
                      activeColor: GhajiniTheme.primaryOrange,
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Messages
                  if (_errorMessage != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(
                          fontSize: 19,
                          color: GhajiniTheme.emergencyRed,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),

                  if (_successMessage != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(
                        _successMessage!,
                        style: const TextStyle(
                          fontSize: 20,
                          color: GhajiniTheme.successGreen,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),

                  // Submit Button
                  BigButton(
                    text: _isSubmitting ? 'Saving Contact...' : 'Save Family / Friend',
                    icon: Icons.check_circle_rounded,
                    backgroundColor: GhajiniTheme.successGreen,
                    textColor: Colors.white,
                    onPressed: _isSubmitting ? null : _submit,
                  ),

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
