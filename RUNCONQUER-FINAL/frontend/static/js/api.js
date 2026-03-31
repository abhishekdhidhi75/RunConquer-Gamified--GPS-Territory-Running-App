/**
 * RunConquer — API Client
 * Handles all HTTP requests to the backend.
 */

const API_BASE = '';  // Same origin

// --- Token Management ---

function getToken() {
  return localStorage.getItem('rc_token');
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('rc_user'));
  } catch {
    return null;
  }
}

function clearAuth() {
  localStorage.removeItem('rc_token');
  localStorage.removeItem('rc_user');
}

// --- HTTP Methods ---

async function apiGet(endpoint) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const res = await fetch(API_BASE + endpoint, { headers });
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  
  return res.json();
}

async function apiPost(endpoint, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const res = await fetch(API_BASE + endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  
  return res.json();
}
