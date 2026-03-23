import { EntityDetail, MapResponse, SearchResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { next: { revalidate: 60 } });
  if (!response.ok) {
    throw new Error(`API request failed for ${path}`);
  }
  return response.json() as Promise<T>;
}

export function fetchEntities(query = ""): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    state: "CA",
    program_category: "procurement",
  });
  return getJson<SearchResponse>(`/search/entities?${params.toString()}`);
}

export function fetchEntity(entityId: string): Promise<EntityDetail> {
  return getJson<EntityDetail>(`/entities/${entityId}`);
}

export function fetchMap(): Promise<MapResponse> {
  const params = new URLSearchParams({
    state: "CA",
    program_category: "procurement",
  });
  return getJson<MapResponse>(`/map/entities?${params.toString()}`);
}
