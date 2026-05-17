import 'package:flutter/foundation.dart' show kIsWeb;

/// Single source of truth for the backend URL.
///
/// Change ONE line below to switch host or port — every screen will
/// pick it up automatically.
///
/// You can also override at run-time without editing files:
///   flutter run --dart-define=API_HOST=192.168.1.50 --dart-define=API_PORT=8000
class ApiConfig {
  /// Backend host (auto-detects emulator vs web vs LAN device).
  ///
  /// Defaults:
  ///   - Web (Chrome)            → 127.0.0.1
  ///   - Android emulator        → 10.0.2.2
  ///   - iOS simulator / desktop → 127.0.0.1
  static const String _envHost = String.fromEnvironment('API_HOST');
  static const String _envPort = String.fromEnvironment('API_PORT', defaultValue: '8000');

  /// Backend port (default 8000). Override with --dart-define=API_PORT=8001
  static int get port => int.tryParse(_envPort) ?? 8000;

  /// The full base URL the app should hit.
  static String get baseUrl {
    if (_envHost.isNotEmpty) {
      return "http://$_envHost:$port";
    }
    if (kIsWeb) {
      return "http://127.0.0.1:$port";
    }
    // Default for Android emulator (host's localhost is 10.0.2.2)
    return "http://10.0.2.2:$port";
  }
}
