
const API_BASE = "/api";

// Reusable function for GET requests
async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`);

  if (!response.ok) {
    let message = `HTTP error: ${response.status}`;

    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep the default error if the response isn't JSON.
    }

    throw new Error(
      typeof message === "string"
        ? message
        : JSON.stringify(message)
    );
  }

  return response.json();
}

// 1. Lakes
export function getLakes() {
  return apiGet("/lakes");
}

export function getLake(lakeId) {
  return apiGet(`/lakes/${encodeURIComponent(lakeId)}`);
}

// 2. Sensors
export function getSensors() {
  return apiGet("/sensors");
}

export function getSensor(sensorId) {
  return apiGet(`/sensors/${encodeURIComponent(sensorId)}`);
}

// 3. All readings (paginated)
export function getReadings(page = 1, size = 10) {
  return apiGet(`/readings?page=${page}&size=${size}`);
}

// 4. Readings for a specific lake (paginated)
export function getLakeReadings(lakeId, page = 1, size = 10) {
  return apiGet(
    `/lakes/${encodeURIComponent(lakeId)}/readings?page=${page}&size=${size}`
  );
}

// 5. Latest reading for a lake
export function getLatestReading(lakeId) {
  return apiGet(
    `/lakes/${encodeURIComponent(lakeId)}/latest-reading`
  );
}

// 6. Aggregate water-quality data
export function getLakeAggregate(lakeId) {
  return apiGet(
    `/${encodeURIComponent(lakeId)}/aggregate`
  );
}

// 7. Individual reading by database ID
export function getReading(dbId) {
  return apiGet(`/readings/${encodeURIComponent(dbId)}`);
}

// 8. Backend health (doesn't use /api)
export async function getHealth() {
  const response = await fetch("/health");

  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.status}`);
  }

  return response.json();
}
