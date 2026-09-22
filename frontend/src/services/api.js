/**
 * API Service for interacting with the Cancer Multi-Agent Backend
 */

const API_BASE = '';

/**
 * Send a question to the multi-agent backend pipeline.
 *
 * @param {string} question - The user's query
 * @returns {Promise<{
 *   question: string,
 *   answer: string,
 *   verification_status: "PASS" | "FAIL" | "UNKNOWN" | string,
 *   sources: Array<{ title?: string, document?: string, page_start?: number, page_end?: number, source_year?: number, source_category?: string, snippet?: string, url?: string }>,
 *   agents_used: string[],
 *   verification_attempts: number,
 *   mode: "mock" | "live" | string,
 *   route?: Record<string, any>
 * }>}
 */
export async function askQuestion(question) {
  const trimmed = question.trim();
  if (!trimmed) {
    throw new Error('Question cannot be empty.');
  }

  const payload = { question: trimmed };

  try {
    const response = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorMessage = `Server error (${response.status})`;
      try {
        const errorData = await response.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // use default error message
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    // If proxy failed or connection refused
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to the backend server (127.0.0.1:8000). Please ensure the FastAPI server is running.');
    }
    throw error;
  }
}

/**
 * Check the health and mode of the backend service.
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (response.ok) {
      const data = await response.json();
      return {
        online: true,
        mode: data.mode || 'unknown',
        status: data.status || 'ok',
      };
    }
    return { online: false, mode: 'offline', status: 'error' };
  } catch {
    return { online: false, mode: 'offline', status: 'unreachable' };
  }
}
