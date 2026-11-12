import React, { useCallback, useEffect, useState } from "react";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { apiGet } from "../api";
import { getCoords } from "../location";
import { useAuth } from "../context/AuthContext";
import { colors, gradients, radius, shadow } from "../theme";
import { Card, SectionTitle } from "../components/ui";
import { FadeInView, PressableScale, PulseDot } from "../components/animated";
import { GlassBackground } from "../components/background";
import { HardwareReading, Weather } from "../types";

export default function HomeScreen({ navigation }: { navigation: any }) {
  const { user } = useAuth();
  const [weather, setWeather] = useState<Weather | null>(null);
  const [hardware, setHardware] = useState<HardwareReading | null>(null);
  const [hwConnected, setHwConnected] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const coords = await getCoords();
      const query = coords ? `?lat=${coords.latitude}&lon=${coords.longitude}` : "";
      const [w, hw] = await Promise.all([
        apiGet<Weather>(`/api/weather${query}`),
        apiGet<{ connected: boolean; reading: HardwareReading | null }>(
          "/api/hardware/latest"
        ),
      ]);
      setWeather(w);
      setHwConnected(hw.connected);
      setHardware(hw.reading);
    } catch {
      // server temporarily unreachable; keep last values
    }
  }, []);

  useEffect(() => {
    (async () => {
      await load();
    })();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const firstName = (user?.full_name || user?.username || "Farmer").split(" ")[0];
  const weatherEmoji =
    weather && (weather.rain_chance > 50 ? "🌧️" : weather.rain_chance > 20 ? "⛅" : "☀️");

  return (
    <GlassBackground>
      <SafeAreaView style={styles.safe} edges={["top"]}>
        <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        }
      >
        <FadeInView>
          <LinearGradient colors={gradients.hero} style={styles.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
            <View style={{ flex: 1 }}>
              <Text style={styles.heroHi}>Namaste, {firstName} 👋</Text>
              <Text style={styles.heroSub}>Your farm at a glance</Text>
              <View style={styles.heroPill}>
                <PulseDot color={hwConnected ? "#86efac" : "#fca5a5"} />
                <Text style={styles.heroPillText}>
                  {hwConnected ? "Sensors live" : "Sensors offline"}
                </Text>
              </View>
            </View>
            <Text style={styles.heroEmoji}>{weatherEmoji || "🌾"}</Text>
          </LinearGradient>
        </FadeInView>

        <FadeInView delay={80}>
          <SectionTitle title="Weather" />
        </FadeInView>
        {weather ? (
          <FadeInView delay={120}>
            <Card>
              <View style={styles.weatherTop}>
                <View>
                  <Text style={styles.weatherLoc}>
                    {weather.location}, {weather.region}
                  </Text>
                  <Text style={styles.weatherTemp}>{Math.round(weather.temp)}°C</Text>
                  <Text style={styles.weatherCond}>{weather.condition}</Text>
                </View>
                <LinearGradient colors={gradients.soft} style={styles.weatherIconCircle}>
                  <Text style={styles.weatherIcon}>{weatherEmoji}</Text>
                </LinearGradient>
              </View>
              <View style={styles.weatherStats}>
                <View style={styles.weatherStat}>
                  <Ionicons name="water-outline" size={16} color={colors.primary} />
                  <Text style={styles.weatherStatText}>{weather.humidity}% humidity</Text>
                </View>
                <View style={styles.weatherStat}>
                  <Ionicons name="umbrella-outline" size={16} color={colors.primary} />
                  <Text style={styles.weatherStatText}>{weather.rain_chance}% rain</Text>
                </View>
                <View style={styles.weatherStat}>
                  <Ionicons name="flag-outline" size={16} color={colors.primary} />
                  <Text style={styles.weatherStatText}>{weather.wind_speed} km/h</Text>
                </View>
              </View>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 14 }}>
                {weather.weekly.map((d) => (
                  <View key={d.day} style={styles.dayBox}>
                    <Text style={styles.dayName}>{d.day}</Text>
                    <Text style={styles.dayIcon}>
                      {d.rain_chance > 50 ? "🌧️" : d.rain_chance > 20 ? "⛅" : "☀️"}
                    </Text>
                    <Text style={styles.dayTemp}>
                      {Math.round(d.max_temp)}° / {Math.round(d.min_temp)}°
                    </Text>
                  </View>
                ))}
              </ScrollView>
              {weather.is_demo ? (
                <Text style={styles.demoNote}>Live weather unavailable — showing estimates</Text>
              ) : null}
            </Card>
          </FadeInView>
        ) : (
          <Card>
            <Text style={styles.muted}>Loading weather...</Text>
          </Card>
        )}

        <FadeInView delay={160}>
          <SectionTitle title="Farm Sensors (ESP32)" />
        </FadeInView>
        <FadeInView delay={200}>
          <Card>
            <View style={styles.hwHeader}>
              <PulseDot color={hwConnected ? "#22c55e" : "#ef4444"} size={12} />
              <Text style={styles.hwStatus}>
                {hwConnected ? "Connected" : hardware ? "Last reading (stale)" : "Offline"}
              </Text>
            </View>
            {hardware ? (
              <>
                <View style={styles.hwGrid}>
                  {[
                    { v: `${Math.round(hardware.soil_moisture)}%`, l: "Soil moisture", i: "water" as const },
                    { v: `${Math.round(hardware.humidity)}%`, l: "Humidity", i: "cloud" as const },
                    {
                      v: hardware.temperature != null ? `${Math.round(hardware.temperature)}°` : "—",
                      l: "Temperature",
                      i: "thermometer" as const,
                    },
                  ].map((m) => (
                    <LinearGradient
                      key={m.l}
                      colors={["rgba(255,255,255,0.65)", "rgba(255,255,255,0.4)"]}
                      style={styles.hwBox}
                    >
                      <Ionicons name={m.i} size={16} color={colors.primary} />
                      <Text style={styles.hwValue}>{m.v}</Text>
                      <Text style={styles.hwLabel}>{m.l}</Text>
                    </LinearGradient>
                  ))}
                </View>
                <Text style={styles.hwDevice}>
                  {hardware.device_id} · {Math.round(hardware.age_seconds)}s ago
                </Text>
              </>
            ) : (
              <Text style={styles.muted}>
                No sensor data yet. Follow hardware/README.md to connect your ESP32.
              </Text>
            )}
          </Card>
        </FadeInView>

        <FadeInView delay={240}>
          <SectionTitle title="Quick Actions" />
        </FadeInView>
        <FadeInView delay={280}>
          <View style={styles.actionsRow}>
            <PressableScale
              style={{ flex: 1 }}
              onPress={() => navigation.navigate("Crop")}
            >
              <LinearGradient colors={gradients.primary} style={styles.actionBtn} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                <Text style={styles.actionEmoji}>🌱</Text>
                <Text style={styles.actionTitle}>Crop Recommendation</Text>
                <Text style={styles.actionDesc}>AI suggests the best crop for your soil</Text>
              </LinearGradient>
            </PressableScale>
            <PressableScale
              style={{ flex: 1 }}
              onPress={() => navigation.navigate("Disease")}
            >
              <LinearGradient colors={gradients.dark} style={styles.actionBtn} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                <Text style={styles.actionEmoji}>🔬</Text>
                <Text style={styles.actionTitle}>Disease Scan</Text>
                <Text style={styles.actionDesc}>Photograph a leaf to detect disease</Text>
              </LinearGradient>
            </PressableScale>
          </View>
        </FadeInView>
      </ScrollView>
      </SafeAreaView>
    </GlassBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "transparent" },
  container: { padding: 16, paddingBottom: 120 },
  hero: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: radius.xl,
    padding: 22,
    marginBottom: 20,
    ...shadow,
  },
  heroHi: { fontSize: 23, fontWeight: "800", color: colors.white },
  heroSub: { fontSize: 13, color: "#a7f3d0", marginTop: 3 },
  heroPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.14)",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginTop: 12,
  },
  heroPillText: { color: "#ecfdf5", fontSize: 12, fontWeight: "600" },
  heroEmoji: { fontSize: 52 },
  weatherTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  weatherLoc: { fontSize: 15, fontWeight: "700", color: colors.text },
  weatherTemp: { fontSize: 40, fontWeight: "800", color: colors.text },
  weatherCond: { fontSize: 14, color: colors.textMuted },
  weatherIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: "center",
    justifyContent: "center",
  },
  weatherIcon: { fontSize: 36 },
  weatherStats: { flexDirection: "row", gap: 16, marginTop: 10 },
  weatherStat: { flexDirection: "row", alignItems: "center", gap: 4 },
  weatherStatText: { fontSize: 13, color: colors.textMuted },
  dayBox: {
    backgroundColor: "rgba(255,255,255,0.55)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.9)",
    borderRadius: radius.md,
    padding: 10,
    marginRight: 8,
    alignItems: "center",
    minWidth: 72,
  },
  dayName: { fontSize: 12, fontWeight: "700", color: colors.primaryDark },
  dayIcon: { fontSize: 20, marginVertical: 4 },
  dayTemp: { fontSize: 11, color: colors.text },
  demoNote: { fontSize: 11, color: colors.textMuted, marginTop: 10 },
  hwHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 },
  hwStatus: { fontSize: 14, fontWeight: "600", color: colors.text },
  hwGrid: { flexDirection: "row", gap: 10 },
  hwBox: {
    flex: 1,
    borderRadius: radius.md,
    padding: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.9)",
  },
  hwValue: { fontSize: 20, fontWeight: "800", color: colors.primaryDark, marginTop: 4 },
  hwLabel: { fontSize: 10, color: colors.textMuted, marginTop: 2, textAlign: "center" },
  hwDevice: { fontSize: 12, color: colors.textMuted, marginTop: 10 },
  actionsRow: { flexDirection: "row", gap: 12 },
  actionBtn: { borderRadius: radius.lg, padding: 16, minHeight: 150, ...shadow },
  actionEmoji: { fontSize: 28 },
  actionTitle: { fontSize: 15, fontWeight: "700", color: colors.white, marginTop: 8 },
  actionDesc: { fontSize: 12, color: "#ecfdf5", marginTop: 4 },
  muted: { color: colors.textMuted, fontSize: 14 },
});
