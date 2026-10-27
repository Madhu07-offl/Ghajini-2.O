import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ghajini_app/core/theme.dart';
import 'package:ghajini_app/providers/app_providers.dart';
import 'package:ghajini_app/services/tts_service.dart';
import 'package:url_launcher/url_launcher.dart';

class CompanionScreen extends ConsumerStatefulWidget {
  const CompanionScreen({super.key});

  @override
  ConsumerState<CompanionScreen> createState() => _CompanionScreenState();
}

class _CompanionScreenState extends ConsumerState<CompanionScreen> {
  final TextEditingController _textController = TextEditingController();
  final TtsService _ttsService = TtsService();

  String _lastMessage = "Hello! I am Ghajini, your memory companion. How can I help you today?";
  String _selectedLang = 'hi'; // Default Hindi
  bool _isLoading = false;
  String? _loadingStatus;
  Timer? _timeoutTimer;
  Map<String, dynamic>? _lastPersonCard;
  List<String> _lastActions = [];
  bool _isSpeaking = false;

  // Confidence confirmation dialog state
  bool _showConfirmation = false;
  String _candidateText = "";

  @override
  void initState() {
    super.initState();
    _initTts();
    _startProactivePolling();
  }

  Future<void> _initTts() async {
    await _ttsService.init();
    _speak(_lastMessage);
  }

  void _startProactivePolling() {
    // Poll proactive companion every 30 seconds
    Timer.periodic(const Duration(seconds: 30), (timer) async {
      if (!mounted) {
        timer.cancel();
        return;
      }
      try {
        final api = ref.read(apiServiceProvider);
        final res = await api.getCompanionProactive();
        if (res['has_message'] == true && res['message'] != null) {
          final msg = res['message'] as Map<String, dynamic>;
          final text = msg['message'] as String? ?? "";
          if (text.isNotEmpty && mounted) {
            setState(() {
              _lastMessage = text;
            });
            _speak(text);
          }
        }
      } catch (_) {}
    });
  }

  Future<void> _speak(String text) async {
    setState(() => _isSpeaking = true);
    await _ttsService.speak(text, lang: _selectedLang);
    if (mounted) {
      setState(() => _isSpeaking = false);
    }
  }

  Future<void> _sendMessage(String text, {String source = 'text'}) async {
    if (text.trim().isEmpty) return;
    _textController.clear();

    setState(() {
      _isLoading = true;
      _loadingStatus = "Let me think...";
      _lastPersonCard = null;
      _lastActions = [];
    });

    // 15-second timeout safety guardrail
    _timeoutTimer?.cancel();
    _timeoutTimer = Timer(const Duration(seconds: 15), () {
      if (_isLoading && mounted) {
        setState(() {
          _isLoading = false;
          _lastMessage = _selectedLang == 'hi'
              ? "मुझे पक्का नहीं पता। क्या मैं आपके परिवार को फोन करूं?"
              : (_selectedLang == 'pa'
                  ? "ਮੈਨੂੰ ਪੱਕਾ ਨਹੀਂ ਪਤਾ। ਕੀ ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਾਂ?"
                  : "I am not sure. Shall I call your family?");
        });
        _speak(_lastMessage);
      }
    });

    try {
      final api = ref.read(apiServiceProvider);
      final res = await api.sendCompanionMessage(
        text: text,
        lang: _selectedLang,
        source: source,
      );

      _timeoutTimer?.cancel();

      if (mounted) {
        final reply = res['reply'] as String? ?? "";
        final person = res['person'] as Map<String, dynamic>?;
        final actions = (res['actions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

        setState(() {
          _isLoading = false;
          _lastMessage = reply;
          _lastPersonCard = person;
          _lastActions = actions;
        });

        // Speak aloud in selected language
        _speak(reply);

        // If action is call_family or show_sos
        if (actions.contains('call_family') || actions.contains('show_sos')) {
          _showEmergencyAlertBanner();
        }
      }
    } catch (_) {
      _timeoutTimer?.cancel();
      if (mounted) {
        setState(() {
          _isLoading = false;
          _lastMessage = _selectedLang == 'hi'
              ? "मुझे पक्का नहीं पता। क्या मैं आपके परिवार को फोन करूं?"
              : (_selectedLang == 'pa'
                  ? "ਮੈਨੂੰ ਪੱਕਾ ਨਹੀਂ ਪਤਾ। ਕੀ ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਾਂ?"
                  : "I am not sure. Shall I call your family?");
        });
        _speak(_lastMessage);
      }
    }
  }

  void _callFamily() async {
    final uri = Uri.parse("tel:+919876543210");
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  void _triggerSos() async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.triggerEmergencyHelp(note: "SOS Button pressed on Companion Screen");
      if (mounted) {
        setState(() {
          _lastMessage = _selectedLang == 'hi'
              ? "मदद आ रही है। आपके परिवार को बता दिया गया है।"
              : (_selectedLang == 'pa'
                  ? "ਮਦਦ ਆ ਰਹੀ ਹੈ। ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਦੱਸ ਦਿੱਤਾ ਗਿਆ ਹੈ।"
                  : "Help is coming. Your family has been notified.");
        });
        _speak(_lastMessage);
      }
    } catch (_) {}
  }

  void _showEmergencyAlertBanner() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: GhajiniTheme.emergencyRed,
        content: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.white, size: 28),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                "Caregiver Alert Dispatched. Your family has been notified.",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        duration: const Duration(seconds: 6),
      ),
    );
  }

  @override
  void dispose() {
    _timeoutTimer?.cancel();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text(
          "Ghajini Memory Companion",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
        ),
        actions: [
          // Language selector
          Container(
            margin: const EdgeInsets.only(right: 8),
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedLang,
                dropdownColor: const Color(0xFF1E293B),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                items: const [
                  DropdownMenuItem(value: 'hi', child: Text("हिंदी (HI)")),
                  DropdownMenuItem(value: 'en', child: Text("English (EN)")),
                  DropdownMenuItem(value: 'pa', child: Text("ਪੰਜਾਬੀ (PA)")),
                ],
                onChanged: (val) {
                  if (val != null) {
                    setState(() => _selectedLang = val);
                  }
                },
              ),
            ),
          ),
          // SOS Button Always Visible
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton.icon(
              onPressed: _triggerSos,
              icon: const Icon(Icons.sos, color: Colors.white, size: 20),
              label: const Text("SOS", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
              style: ElevatedButton.styleFrom(
                backgroundColor: GhajiniTheme.emergencyRed,
                elevation: 4,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Top Section: Avatar & Message Display
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    // Large Friendly Avatar Circle
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF1E3A8A),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF1E3A8A).withOpacity(0.25),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: const Center(
                        child: Text("🤖", style: TextStyle(fontSize: 48)),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Confirmation banner if speech confidence was low
                    if (_showConfirmation) ...[
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF3C7),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFF59E0B)),
                        ),
                        child: Column(
                          children: [
                            Text(
                              "Did you ask: '$_candidateText'?",
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF92400E)),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                ElevatedButton(
                                  onPressed: () {
                                    setState(() => _showConfirmation = false);
                                    _sendMessage(_candidateText);
                                  },
                                  style: ElevatedButton.styleFrom(backgroundColor: GhajiniTheme.successGreen),
                                  child: const Text("Yes", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                ),
                                const SizedBox(width: 16),
                                OutlinedButton(
                                  onPressed: () => setState(() => _showConfirmation = false),
                                  child: const Text("No", style: TextStyle(fontWeight: FontWeight.bold)),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Big Friendly Message Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFFE2E8F0), width: 1.5),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.04),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (_isLoading) ...[
                            Row(
                              children: [
                                const SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(strokeWidth: 2.5),
                                ),
                                const SizedBox(width: 14),
                                Text(
                                  _loadingStatus ?? "Let me think...",
                                  style: const TextStyle(fontSize: 20, color: Color(0xFF64748B), fontStyle: FontStyle.italic),
                                ),
                              ],
                            ),
                          ] else ...[
                            Text(
                              _lastMessage,
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF1E293B),
                                height: 1.45,
                              ),
                            ),
                          ],
                          const SizedBox(height: 14),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              IconButton(
                                icon: Icon(
                                  _isSpeaking ? Icons.volume_up : Icons.volume_down,
                                  color: const Color(0xFF1E3A8A),
                                  size: 32,
                                ),
                                onPressed: () => _speak(_lastMessage),
                                tooltip: "Replay speech",
                              ),
                              ElevatedButton.icon(
                                onPressed: _callFamily,
                                icon: const Icon(Icons.phone, size: 20, color: Colors.white),
                                label: const Text("Call Family", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF0F172A),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    // Photo card if person or place was mentioned
                    if (_lastPersonCard != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF4),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFBBF7D0)),
                        ),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 30,
                              backgroundColor: const Color(0xFF1E3A8A),
                              child: Text(
                                (_lastPersonCard!['name'] as String? ?? "P").substring(0, 1),
                                style: const TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.bold),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    "${_lastPersonCard!['name']} (${_lastPersonCard!['relationship']})",
                                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF166534)),
                                  ),
                                  if (_lastPersonCard!['notes'] != null)
                                    Text(
                                      _lastPersonCard!['notes'],
                                      style: const TextStyle(fontSize: 14, color: Color(0xFF1E293B)),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // Bottom Section: Three Quick Buttons + Push-to-Talk Mic + Text Input
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 10,
                    offset: const Offset(0, -3),
                  ),
                ],
              ),
              child: Column(
                children: [
                  // Three Quick Buttons
                  Row(
                    children: [
                      Expanded(
                        child: _QuickActionButton(
                          label: "Who is this?",
                          icon: Icons.person_search,
                          onPressed: () => _sendMessage("Who is this?"),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _QuickActionButton(
                          label: "What's next?",
                          icon: Icons.event_note,
                          onPressed: () => _sendMessage("What is next today?"),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _QuickActionButton(
                          label: "Call family",
                          icon: Icons.phone_forwarded,
                          onPressed: _callFamily,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Push to talk large Mic Button (64dp+)
                  Center(
                    child: GestureDetector(
                      onTap: () {
                        // Push to talk action: triggers gentle prompt or voice listen
                        _sendMessage("What day is it today?", source: 'voice');
                      },
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: const Color(0xFF1E3A8A),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF1E3A8A).withOpacity(0.35),
                              blurRadius: 16,
                              offset: const Offset(0, 6),
                            ),
                          ],
                        ),
                        child: const Icon(Icons.mic, color: Colors.white, size: 38),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Text input field with send button
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _textController,
                          style: const TextStyle(fontSize: 16),
                          decoration: InputDecoration(
                            hintText: "Type or ask Ghajini a question...",
                            contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
                            ),
                          ),
                          onSubmitted: (val) => _sendMessage(val),
                        ),
                      ),
                      const SizedBox(width: 10),
                      IconButton(
                        onPressed: () => _sendMessage(_textController.text),
                        icon: const Icon(Icons.send_rounded, color: Color(0xFF1E3A8A), size: 30),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  const _QuickActionButton({
    required this.label,
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFFF1F5F9),
        foregroundColor: const Color(0xFF0F172A),
        elevation: 0,
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: Color(0xFFCBD5E1)),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 22, color: const Color(0xFF1E3A8A)),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700), textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
