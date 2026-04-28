import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class DeviceService {
  static const String _key = "device_id";

  static Future<String> getDeviceId() async {
    final prefs = await SharedPreferences.getInstance();

    String? deviceId = prefs.getString(_key);

    if (deviceId != null) {
      return deviceId;
    }

    // generate baru
    const uuid = Uuid();
    deviceId = uuid.v4();

    await prefs.setString(_key, deviceId);

    return deviceId;
  }
}