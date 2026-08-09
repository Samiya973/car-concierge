export interface UserPreferences {
  intent?: 'buy' | 'rent' | null;
  use_case?: string | null;
  category?: string | null;
  budget_max?: number | null;
  target_date?: string | null;
  seats?: number | null;
  location?: string | null;
  fuel_type?: string | null;
}

export interface CarListing {
  id: string;
  brand: string;
  model: string;
  category: string;
  year: number;
  price: number;
  intent: string;
  mileage_km: number;
  condition: string;
  seats: number;
  fuel_type: string;
  location: string;
  available_from: string;
  dealer: string;
  image_seed: string;
}

export interface RankedListing {
  listing: CarListing;
  score: number;
  explanation: string;
}

export interface ChatMessage {
  sender: 'user' | 'agent';
  text: string;
}

export interface ChatApiResponse {
  session_id: string;
  stage: 'interview' | 'research' | 'recommend' | 'form' | 'payment' | 'done';
  reply: string;
  preferences: UserPreferences;
  results: RankedListing[];
  reasoning_log: { ts: number; text: string }[];
}