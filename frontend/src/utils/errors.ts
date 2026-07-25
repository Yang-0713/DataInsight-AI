import axios from 'axios'

export function getApiErrorMessage(
  error: unknown,
  fallback = '请求失败，请稍后重试',
): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0]?.msg ?? fallback
    }
  }
  return fallback
}
