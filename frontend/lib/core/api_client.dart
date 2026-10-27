import 'package:dio/dio.dart';
import 'package:ghajini_app/core/constants.dart';

class ApiClient {
  static Dio createDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 20),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException e, handler) {
          String friendlyMessage;

          switch (e.type) {
            case DioExceptionType.connectionTimeout:
            case DioExceptionType.receiveTimeout:
            case DioExceptionType.sendTimeout:
              friendlyMessage =
                  "The connection took a little longer than usual. Please check your network.";
              break;
            case DioExceptionType.connectionError:
              friendlyMessage =
                  "I cannot connect to your memory server right now. Please ensure the server is turned on.";
              break;
            case DioExceptionType.badResponse:
              final statusCode = e.response?.statusCode;
              if (statusCode == 400) {
                friendlyMessage = e.response?.data?['detail'] ??
                    "Some required information is missing. Please check and try again.";
              } else if (statusCode == 404) {
                friendlyMessage = "We couldn't find that memory or person.";
              } else {
                friendlyMessage =
                    "I had trouble with that request. Please try again shortly.";
              }
              break;
            default:
              friendlyMessage =
                  "Something unexpected occurred. Please try again or ask your family.";
          }

          final friendlyError = DioException(
            requestOptions: e.requestOptions,
            response: e.response,
            type: e.type,
            error: friendlyMessage,
            message: friendlyMessage,
          );
          return handler.next(friendlyError);
        },
      ),
    );

    return dio;
  }
}
