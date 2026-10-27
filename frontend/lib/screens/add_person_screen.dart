import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/providers/app_providers.dart';

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
  String? _photoPath;
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
        setState(() => _photoPath = file.path);
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

      // Upload face photo if provided
      if (_photoPath != null) {
        await api.uploadPersonFace(
          personId: person.id,
          filePath: _photoPath!,
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
        _errorMessage = "Could not register person. Please try again.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Family or Friend'),
        backgroundColor: AppTheme.primaryDark,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Caregiver Portal: Add Contact',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Enter their details so the companion can recognize and speak about them.',
                  style: TextStyle(fontSize: 18, color: Colors.black54),
                ),
                const SizedBox(height: 24),

                // Name field
                TextFormField(
                  controller: _nameController,
                  style: const TextStyle(fontSize: 22),
                  decoration: const InputDecoration(
                    labelText: 'Full Name *',
                    hintText: 'e.g., Priya or Dr. Sharma',
                  ),
                  validator: (val) =>
                      val == null || val.trim().isEmpty ? 'Please enter a name' : null,
                ),
                const SizedBox(height: 20),

                // Relationship field
                TextFormField(
                  controller: _relationshipController,
                  style: const TextStyle(fontSize: 22),
                  decoration: const InputDecoration(
                    labelText: 'Relationship *',
                    hintText: 'e.g., Daughter, Son, Doctor',
                  ),
                  validator: (val) =>
                      val == null || val.trim().isEmpty ? 'Please enter relationship' : null,
                ),
                const SizedBox(height: 20),

                // Notes field
                TextFormField(
                  controller: _notesController,
                  style: const TextStyle(fontSize: 20),
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Helpful Notes (optional)',
                    hintText: 'e.g., Lives in Bangalore, visits on Sundays',
                  ),
                ),
                const SizedBox(height: 24),

                // Photo Picker Section
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Face Photo for Recognition',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        if (_photoPath != null) ...[
                          Center(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: kIsWeb
                                  ? Image.network(_photoPath!, height: 160)
                                  : Image.file(File(_photoPath!), height: 160),
                            ),
                          ),
                          const SizedBox(height: 12),
                        ],
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () => _pickPhoto(ImageSource.camera),
                                icon: const Icon(Icons.camera_alt),
                                label: const Text('Camera', style: TextStyle(fontSize: 18)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () => _pickPhoto(ImageSource.gallery),
                                icon: const Icon(Icons.photo_library),
                                label: const Text('Gallery', style: TextStyle(fontSize: 18)),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // Mandatory Consent Checkbox
                Card(
                  color: const Color(0xFFF3F4F6),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(
                      color: _consentGiven ? AppTheme.gentleGreen : Colors.grey,
                      width: 1.5,
                    ),
                  ),
                  child: CheckboxListTile(
                    value: _consentGiven,
                    onChanged: (val) => setState(() => _consentGiven = val ?? false),
                    title: const Text(
                      'I confirm consent has been provided to store this person\'s name and photo for face recognition and patient assistance.',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                    ),
                    controlAffinity: ListTileControlAffinity.leading,
                    activeColor: AppTheme.primaryDark,
                  ),
                ),

                const SizedBox(height: 24),

                if (_errorMessage != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(fontSize: 18, color: Colors.red, fontWeight: FontWeight.bold),
                    ),
                  ),

                if (_successMessage != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(
                      _successMessage!,
                      style: const TextStyle(
                        fontSize: 20,
                        color: AppTheme.gentleGreen,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),

                // Submit Button
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.gentleGreen,
                    minimumSize: const Size(double.infinity, 68),
                  ),
                  onPressed: _isSubmitting ? null : _submit,
                  child: _isSubmitting
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text(
                          'Save Person',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
