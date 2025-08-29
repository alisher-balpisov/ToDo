
// A global way to get and set tokens. This would typically be managed by a context or state manager.
// For simplicity in this single-file generation, we use a simple object.
export const tokenManager = {
  getAccessToken: (): string | null => localStorage.getItem('accessToken'),
  getRefreshToken: (): string | null => localStorage.getItem('refreshToken'),
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  },
  clearTokens: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
};

const API_BASE_URL = 'https://todo-6-9yr1.onrender.com'; // Replace with your actual backend URL

let isRefreshing = false;
let failedQueue: { resolve: (value: unknown) => void; reject: (reason?: any) => void; }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

interface ApiServiceOptions extends RequestInit {
    responseType?: 'json' | 'blob';
}

const apiService = async <T,>(endpoint: string, options: ApiServiceOptions = {}): Promise<T> => {
  const token = tokenManager.getAccessToken();
  const { responseType, ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
   if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }


  const config: RequestInit = {
    ...fetchOptions,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (response.status === 401 && !endpoint.includes('/refresh')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
        .then(newToken => {
            headers.set('Authorization', `Bearer ${newToken as string}`);
            return apiService<T>(endpoint, {...options, headers});
        });
      }

      isRefreshing = true;
      const refreshToken = tokenManager.getRefreshToken();
      if (!refreshToken) {
        tokenManager.clearTokens();
        window.location.reload(); // Force re-render to show login
        throw new Error('Session expired');
      }

      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${refreshToken}`,
          },
        });

        if (!refreshResponse.ok) {
           throw new Error('Failed to refresh token');
        }

        const newTokens = await refreshResponse.json();
        tokenManager.setTokens(newTokens.access_token, newTokens.refresh_token);
        processQueue(null, newTokens.access_token);
        
        headers.set('Authorization', `Bearer ${newTokens.access_token}`);
        return await apiService<T>(endpoint, {...options, headers});

      } catch (e) {
        processQueue(e, null);
        tokenManager.clearTokens();
        window.location.reload();
        throw e;
      } finally {
        isRefreshing = false;
      }
    }

    if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
            // Try to parse error as JSON, which is common for APIs
            const errorData = await response.json();
            errorMessage = errorData.detail || JSON.stringify(errorData);
        } catch (e) {
            // If parsing fails, it's not a JSON error, so use the response text
            const textError = await response.text();
            if (textError) {
               errorMessage = textError;
            }
        }
        throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null as T;
    }

    if (responseType === 'blob') {
        return response.blob() as Promise<T>;
    }

    return response.json() as Promise<T>;
  } catch (error) {
    console.error('API service error:', error);
    throw error;
  }
};

export default apiService;
