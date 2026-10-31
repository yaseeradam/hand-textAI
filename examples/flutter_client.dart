import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class HandAiApiClient {
  final String baseUrl;
  final String? apiKey;

  HandAiApiClient({
    this.baseUrl = 'http://localhost:8000',
    this.apiKey = 'sk-handai-development-key',
  });

  Map<String, String> get _headers => {
        'Accept': 'application/json',
        if (apiKey != null && apiKey!.isNotEmpty) 'X-API-Key': apiKey!,
      };

  /// Check server health
  Future<Map<String, dynamic>> checkHealth() async {
    final response = await http.get(
      Uri.parse('$baseUrl/health'),
      headers: _headers,
    );
    return jsonDecode(response.body);
  }

  /// Recognize handwritten text from a File
  Future<Map<String, dynamic>> recognizeImageFile(File file) async {
    final bytes = await file.readAsBytes();
    final base64String = base64Encode(bytes);

    final response = await http.post(
      Uri.parse('$baseUrl/v1/ocr/recognize'),
      headers: {
        ..._headers,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'image_base64': base64String,
        'mode': 'handwritten',
        'enhance_contrast': true,
        'auto_correct_common_errors': true,
      }),
    );

    return jsonDecode(response.body);
  }

  /// Direct multipart file upload
  Future<Map<String, dynamic>> uploadImageFile(File file) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/v1/ocr/upload'),
    );

    request.headers.addAll(_headers);
    request.fields['mode'] = 'handwritten';
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return jsonDecode(response.body);
  }
}
