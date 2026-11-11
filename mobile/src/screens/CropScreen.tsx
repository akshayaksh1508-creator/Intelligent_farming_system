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
import { colors, gradients, radius, shadow } from "../theme";
import { Card, Chip, PrimaryButton, SectionTitle } from "../components/ui";
import { FadeInView } from "../components/animated";
import { GlassBackground } from "../components/background";
import { CropResult } from "../types";

interface SourceEntry {
  value: number | string;
  source: string;
  note: string;
  unit: string;
}

interface AutoCropResponse {
  success: boolean;
  result: CropResult;
  sources: Record<string, SourceEntry>;
  sensor_connected: boolean;
  season: string;
}

const SOURCE_META: Record<string, { label: string; icon: keyof typeof Ionicons.glyphMap }> = {
  temperature: { label: "Temperature", icon: "thermometer" },
  humidity: { label: "Humidity", icon: "water" },
  rainfall: { label: "Rainfall", icon: "rainy" },
  nitrogen: { label: "Nitrogen (N)", icon: "flask" },
  phosphorus: { label: "Phosphorus (P)", icon: "flask" },
  potassium: { label: "Potassium (K)", icon: "flask" },
  ph: { label: "Soil pH", icon: "color-fill" },
  soil_type: { label: "Soil Type", icon: "layers" },
  season: { label: "Season", icon: "calendar" },
  land_area: { label: "Land Area", icon: "resize" },
  soil_moisture: { label: "Soil Moisture (info)", icon: "water" },
};

const SOURCE_ORDER = [
  "temperature",
  "humidity",
  "rainfall",
  "nitrogen",
  "phosphorus",
  "potassium",
  "ph",
  "soil_type",
  "season",
  "land_area",
  "soil_moisture",
];

function sourceColor(source: string): string {
  if (source.startsWith("ESP32")) return "#059669";
  if (source.startsWith("Weather") || source.startsWith("Auto")) return "#0284c7";
  return colors.textMuted;
}

export default function CropScreen() {
  const [data, setData] = useState<AutoCropResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const coords = await getCoords();
      const query = coords ? `?lat=${coords.latitude}&lon=${coords.longitude}` : "";
      const res = await apiGet<AutoCropResponse>(`/api/crop/auto${query}`);
      setData(res);
    } catch {
      setError("Could not reach the server. Check the server address in Settings.");
    }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await load();
      setLoading(false);
    })();
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const sources = data?.sources || {};
  const keys = SOURCE_ORDER.filter((k) => sources[k]);

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
            <Text style={styles.heroEmoji}>🌱</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>Crop Recommendation</Text>
              <Text style={styles.subtitle}>
                Values are collected automatically from your ESP32 sensor, live weather at
                your location, and seasonal defaults.
              </Text>
            </View>
          </LinearGradient>
        </FadeInView>

        {data ? (
          <FadeInView delay={100}>
            <View
              style={[
                styles.sensorBanner,
                {
                  backgroundColor: data.sensor_connected
                    ? "rgba(220,252,231,0.75)"
                    : "rgba(254,243,199,0.75)",
                  borderColor: data.sensor_connected
                    ? "rgba(134,239,172,0.9)"
                    : "rgba(252,211,77,0.9)",
                },
              ]}
            >
              <Ionicons
                name={data.sensor_connected ? "radio" : "warning"}
                size={18}
                color={data.sensor_connected ? "#166534" : "#92400e"}
              />
              <Text
                style={[
                  styles.sensorBannerText,
                  { color: data.sensor_connected ? "#166534" : "#92400e" },
                ]}
              >
                {data.sensor_connected
                  ? "ESP32 sensor connected — live sensor values in use"
                  : "ESP32 offline — using weather & seasonal defaults"}
              </Text>
            </View>
          </FadeInView>
        ) : null}

        <FadeInView delay={150}>
          <SectionTitle title="Auto-Collected Values" />
        </FadeInView>
        {loading ? (
          <Card>
            <Text style={styles.muted}>Collecting sensor and weather data...</Text>
          </Card>
        ) : data ? (
          <FadeInView delay={180}>
            <Card>
              {keys.map((k, i) => {
                const s = sources[k];
                const meta = SOURCE_META[k];
                const num =
                  typeof s.value === "number" ? String(Math.round(s.value * 10) / 10) : s.value;
                return (
                  <View key={k} style={[styles.srcRow, i > 0 && styles.srcRowBorder]}>
                    <View style={styles.srcIcon}>
                      <Ionicons name={meta.icon} size={15} color={colors.primary} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.srcLabel}>{meta.label}</Text>
                      <View style={styles.srcBadge}>
                        <View style={[styles.srcDot, { backgroundColor: sourceColor(s.source) }]} />
                        <Text style={[styles.srcBadgeText, { color: sourceColor(s.source) }]}>
                          {s.source}
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.srcValue}>
                      {num}
                      {s.unit ? ` ${s.unit}` : ""}
                    </Text>
                  </View>
                );
              })}
            </Card>
          </FadeInView>
        ) : null}

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <FadeInView delay={220}>
          <PrimaryButton title="Get AI Recommendation" onPress={load} loading={loading} />
        </FadeInView>

        {data?.result ? (
          <FadeInView delay={280} distance={24}>
            <View style={styles.resultWrap}>
              <LinearGradient colors={gradients.primary} style={styles.resultCard} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                <View style={styles.resultHeader}>
                  <Text style={styles.resultEmoji}>🌾</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.resultLabel}>AI RECOMMENDED CROP</Text>
                    <Text style={styles.resultCrop}>{data.result.recommended_crop}</Text>
                    <Text style={styles.resultConfidence}>
                      {data.result.confidence}% confidence · {data.season} season
                    </Text>
                  </View>
                </View>

                <View style={styles.metricsRow}>
                  <View style={styles.metricBox}>
                    <Text style={styles.metricValue}>{data.result.expected_yield} q</Text>
                    <Text style={styles.metricLabel}>Expected yield</Text>
                  </View>
                  <View style={styles.metricBox}>
                    <Text style={styles.metricValue}>
                      ₹{data.result.expected_profit.toLocaleString("en-IN")}
                    </Text>
                    <Text style={styles.metricLabel}>Expected profit</Text>
                  </View>
                </View>
              </LinearGradient>

              <Card style={styles.detailsCard}>
                <ResultRow icon="flask-outline" label="Fertilizer" value={data.result.fertilizer} />
                <ResultRow
                  icon="water-outline"
                  label="Water needed"
                  value={data.result.water_requirement}
                />
                <ResultRow
                  icon="time-outline"
                  label="Harvest in"
                  value={data.result.harvest_time}
                />

                <Text style={styles.altLabel}>Also suitable</Text>
                <View style={styles.altRow}>
                  {data.result.alternative_crops.map((c) => (
                    <Chip key={c} label={c} />
                  ))}
                </View>
              </Card>
            </View>
          </FadeInView>
        ) : null}
      </ScrollView>
      </SafeAreaView>
    </GlassBackground>
  );
}

function ResultRow({
  icon,
  label,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
}) {
  return (
    <View style={styles.resultRow}>
      <View style={styles.resultIcon}>
        <Ionicons name={icon} size={16} color={colors.primary} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.resultRowLabel}>{label}</Text>
        <Text style={styles.resultRowValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "transparent" },
  container: { padding: 16, paddingBottom: 120 },
  hero: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderRadius: radius.xl,
    padding: 18,
    marginBottom: 16,
    ...shadow,
  },
  heroEmoji: { fontSize: 40 },
  title: { fontSize: 20, fontWeight: "800", color: colors.white },
  subtitle: { fontSize: 12, color: "#a7f3d0", marginTop: 4, lineHeight: 17 },
  sensorBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: radius.md,
    borderWidth: 1,
    padding: 12,
    marginBottom: 16,
  },
  sensorBannerText: { flex: 1, fontSize: 13, fontWeight: "600" },
  srcRow: { flexDirection: "row", alignItems: "center", paddingVertical: 10, gap: 10 },
  srcRowBorder: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  srcIcon: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  srcLabel: { fontSize: 13, fontWeight: "700", color: colors.text, marginBottom: 3 },
  srcValue: { fontSize: 15, fontWeight: "800", color: colors.primaryDark },
  srcBadge: { flexDirection: "row", alignItems: "center", gap: 5 },
  srcDot: { width: 7, height: 7, borderRadius: 4 },
  srcBadgeText: { fontSize: 11, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: 14 },
  error: { color: colors.danger, fontSize: 13, marginBottom: 10 },
  resultWrap: { marginTop: 16 },
  resultCard: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    padding: 18,
    ...shadow,
  },
  resultHeader: { flexDirection: "row", alignItems: "center", gap: 12 },
  resultEmoji: { fontSize: 44 },
  resultLabel: { fontSize: 11, fontWeight: "700", color: "#a7f3d0", letterSpacing: 1 },
  resultCrop: { fontSize: 26, fontWeight: "800", color: colors.white, marginTop: 2 },
  resultConfidence: { fontSize: 13, color: "#d1fae5", marginTop: 3 },
  metricsRow: { flexDirection: "row", gap: 10, marginTop: 14 },
  metricBox: {
    flex: 1,
    backgroundColor: "rgba(255,255,255,0.14)",
    borderRadius: 12,
    padding: 12,
  },
  metricValue: { fontSize: 16, fontWeight: "800", color: colors.white },
  metricLabel: { fontSize: 11, color: "#d1fae5", marginTop: 2 },
  detailsCard: {
    borderTopLeftRadius: 0,
    borderTopRightRadius: 0,
    borderBottomLeftRadius: radius.lg,
    borderBottomRightRadius: radius.lg,
    marginTop: 0,
  },
  resultRow: { flexDirection: "row", alignItems: "flex-start", marginBottom: 12 },
  resultIcon: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 10,
  },
  resultRowLabel: { fontSize: 11, color: colors.textMuted },
  resultRowValue: { fontSize: 14, color: colors.text, marginTop: 1 },
  altLabel: { fontSize: 13, fontWeight: "700", color: colors.text, marginTop: 4, marginBottom: 8 },
  altRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
});
