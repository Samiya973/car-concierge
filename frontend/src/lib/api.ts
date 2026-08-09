import { ChatApiResponse } from '@/types';

const API_BASE = 'http://127.0.0.1:8000/api';

export async function sendMessageToAgent(message: string, sessionId?: string): Promise<ChatApiResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    throw new Error('Failed to connect to the Matchmaker agent.');
  }

  return res.json();
}

export async function submitBooking(bookingData: {
  session_id: string;
  listing_id: string;
  full_name: string;
  email: string;
  phone: string;
}) {
  const res = await fetch(`${API_BASE}/book`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookingData),
  });

  if (!res.ok) {
    throw new Error('Booking submission failed.');
  }

  return res.json();
}