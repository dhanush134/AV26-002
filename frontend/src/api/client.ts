const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | object | null;
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const headers = new Headers(options.headers);
  const hasJsonBody = options.body && typeof options.body === "object" && !(options.body instanceof FormData);

  if (hasJsonBody) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: hasJsonBody ? JSON.stringify(options.body) : (options.body as BodyInit | null | undefined),
  });

  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await response.json().catch(() => ({})) : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status);
  }

  return data as T;
};

export const apiBaseUrl = API_BASE_URL;
