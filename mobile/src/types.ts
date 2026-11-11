export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  phone: string;
  role: string;
  state: string;
  district?: string;
  farm_name?: string;
  farm_size?: number;
  primary_crop?: string;
  profile_completed: boolean;
  is_approved: boolean;
  is_rejected: boolean;
}

export interface WeatherDay {
  day: string;
  max_temp: number;
  min_temp: number;
  condition: string;
  rain_chance: number;
}

export interface Weather {
  location: string;
  region: string;
  temp: number;
  feels_like: number;
  humidity: number;
  wind_speed: number;
  pressure: number;
  condition: string;
  rain_chance: number;
  sunrise: string;
  sunset: string;
  is_demo: boolean;
  weekly: WeatherDay[];
}

export interface HardwareReading {
  device_id: string;
  soil_moisture: number;
  humidity: number;
  temperature: number | null;
  received_at: string;
  age_seconds: number;
  connected: boolean;
}

export interface CropResult {
  recommended_crop: string;
  confidence: number;
  expected_yield: number;
  expected_profit: number;
  fertilizer: string;
  water_requirement: string;
  harvest_time: string;
  alternative_crops: string[];
}

export interface DiseaseResult {
  plant_type: string;
  disease_name: string;
  severity?: string;
  confidence: number;
  symptoms: string;
  treatment: string;
  medicine: string;
  organic_solution: string;
  preventive_measures: string;
  is_healthy: boolean;
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  category: string;
  price: number;
  unit: string;
  emoji?: string;
  brand?: string;
  is_organic?: boolean;
}

export interface MarketPrice {
  crop: string;
  price: number;
  unit: string;
  change_pct: number;
  trend: "up" | "down" | "stable";
  market: string;
}
