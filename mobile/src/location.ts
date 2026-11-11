import * as Location from "expo-location";

let cached: { latitude: number; longitude: number } | null = null;

export async function getCoords(): Promise<{ latitude: number; longitude: number } | null> {
  if (cached) return cached;
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return null;

    const last = await Location.getLastKnownPositionAsync({ maxAge: 10 * 60 * 1000 });
    if (last) {
      cached = { latitude: last.coords.latitude, longitude: last.coords.longitude };
      return cached;
    }

    const pos = await Promise.race([
      Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Low }),
      new Promise<null>((resolve) => setTimeout(() => resolve(null), 8000)),
    ]);
    if (pos) {
      cached = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
    }
    return cached;
  } catch {
    return null;
  }
}
