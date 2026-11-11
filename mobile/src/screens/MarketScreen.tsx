import React, { useCallback, useEffect, useState } from "react";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { apiGet } from "../api";
import { getCoords } from "../location";
import { colors, gradients, radius, shadow } from "../theme";
import { Card, SectionTitle } from "../components/ui";
import { FadeInView } from "../components/animated";
import { GlassBackground } from "../components/background";
import { MarketPrice, Product } from "../types";

const CATEGORIES = [
  { label: "All", value: "all" },
  { label: "Seeds", value: "seeds" },
  { label: "Fertilizers", value: "fertilizers" },
  { label: "Organic", value: "organic" },
  { label: "Irrigation", value: "irrigation" },
  { label: "Machinery", value: "machinery" },
];

export default function MarketScreen() {
  const [prices, setPrices] = useState<MarketPrice[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [category, setCategory] = useState("all");
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const coords = await getCoords();
      const query = coords ? `?lat=${coords.latitude}&lon=${coords.longitude}` : "";
      const [prods, stats] = await Promise.all([
        apiGet<Product[]>("/api/marketplace/products"),
        apiGet<{ prices: MarketPrice[] }>(`/api/dashboard/stats${query}`),
      ]);
      setProducts(prods);
      setPrices(stats.prices || []);
      setError("");
    } catch {
      setError("Could not reach the server. Check the server address in Settings.");
    }
  }, []);

  useEffect(() => {
    (async () => {
      await load();
    })();
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const filtered = category === "all" ? products : products.filter((p) => p.category === category);

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
            <Text style={styles.heroEmoji}>🛒</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>Marketplace</Text>
              <Text style={styles.subtitle}>Today’s mandi prices and farm supplies</Text>
            </View>
          </LinearGradient>
        </FadeInView>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <FadeInView delay={100}>
          <SectionTitle title="Today’s Market Prices" />
        </FadeInView>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {prices.map((p, i) => (
            <FadeInView key={p.crop} delay={120 + i * 40}>
              <View style={styles.priceCard}>
                <Text style={styles.priceCrop}>{p.crop}</Text>
                <Text style={styles.priceValue}>₹{p.price.toLocaleString("en-IN")}</Text>
                <Text style={styles.priceUnit}>per {p.unit}</Text>
                <View style={styles.priceTrend}>
                  <Ionicons
                    name={p.trend === "up" ? "arrow-up" : p.trend === "down" ? "arrow-down" : "remove"}
                    size={12}
                    color={p.trend === "up" ? "#16a34a" : p.trend === "down" ? colors.danger : colors.textMuted}
                  />
                  <Text
                    style={[
                      styles.priceChange,
                      {
                        color:
                          p.trend === "up" ? "#16a34a" : p.trend === "down" ? colors.danger : colors.textMuted,
                      },
                    ]}
                  >
                    {p.change_pct}%
                  </Text>
                </View>
                <Text style={styles.priceMarket} numberOfLines={1}>
                  {p.market}
                </Text>
              </View>
            </FadeInView>
          ))}
        </ScrollView>

        <FadeInView delay={160}>
          <SectionTitle title="Farm Supplies" />
        </FadeInView>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.catRow}>
          {CATEGORIES.map((c) => (
            <TouchableOpacity
              key={c.value}
              style={[styles.catChip, category === c.value && styles.catChipActive]}
              onPress={() => setCategory(c.value)}
              activeOpacity={0.7}
            >
              <Text style={[styles.catText, category === c.value && styles.catTextActive]}>
                {c.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {filtered.map((p, i) => (
          <FadeInView key={p.id} delay={Math.min(i * 45, 360)} distance={14}>
            <Card style={styles.productCard}>
              <LinearGradient colors={gradients.soft} style={styles.productEmojiCircle}>
                <Text style={styles.productEmoji}>{p.emoji || "📦"}</Text>
              </LinearGradient>
              <View style={{ flex: 1 }}>
                <View style={styles.productTop}>
                  <Text style={styles.productName}>{p.name}</Text>
                  {p.is_organic ? <Text style={styles.organicBadge}>Organic</Text> : null}
                </View>
                <Text style={styles.productBrand}>{p.brand || "Farm Wise"}</Text>
                <Text style={styles.productPrice}>
                  ₹{p.price.toLocaleString("en-IN")}
                  <Text style={styles.productUnit}> / {p.unit}</Text>
                </Text>
              </View>
            </Card>
          </FadeInView>
        ))}
        {filtered.length === 0 && !error ? (
          <Text style={styles.muted}>No products in this category yet.</Text>
        ) : null}
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
    gap: 12,
    borderRadius: radius.xl,
    padding: 18,
    marginBottom: 16,
    ...shadow,
  },
  heroEmoji: { fontSize: 40 },
  title: { fontSize: 20, fontWeight: "800", color: colors.white },
  subtitle: { fontSize: 12, color: "#a7f3d0", marginTop: 4 },
  error: { color: colors.danger, fontSize: 13, marginBottom: 8 },
  priceCard: {
    backgroundColor: "rgba(255,255,255,0.6)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.9)",
    borderRadius: radius.lg,
    padding: 14,
    minWidth: 150,
    marginRight: 10,
    marginBottom: 4,
    ...shadow,
  },
  priceCrop: { fontSize: 14, fontWeight: "700", color: colors.text },
  priceValue: { fontSize: 20, fontWeight: "800", color: colors.primaryDark, marginTop: 4 },
  priceUnit: { fontSize: 11, color: colors.textMuted },
  priceTrend: { flexDirection: "row", alignItems: "center", gap: 3, marginTop: 6 },
  priceChange: { fontSize: 12, fontWeight: "600" },
  priceMarket: { fontSize: 11, color: colors.textMuted, marginTop: 4 },
  catRow: { flexDirection: "row", marginBottom: 12 },
  catChip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 999,
    marginRight: 8,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.9)",
    backgroundColor: "rgba(255,255,255,0.6)",
  },
  catChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    shadowColor: "#047857",
    shadowOpacity: 0.3,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },
  catText: { fontSize: 13, color: colors.textMuted },
  catTextActive: { color: colors.white, fontWeight: "700" },
  productCard: { flexDirection: "row", alignItems: "center", gap: 12 },
  productEmojiCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
  },
  productEmoji: { fontSize: 26 },
  productTop: { flexDirection: "row", alignItems: "center", gap: 8 },
  productName: { fontSize: 15, fontWeight: "700", color: colors.text, flexShrink: 1 },
  organicBadge: {
    fontSize: 10,
    fontWeight: "700",
    color: "#166534",
    backgroundColor: colors.primaryLight,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    overflow: "hidden",
  },
  productBrand: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  productPrice: { fontSize: 15, fontWeight: "800", color: colors.primaryDark, marginTop: 4 },
  productUnit: { fontSize: 12, fontWeight: "400", color: colors.textMuted },
  muted: { color: colors.textMuted, fontSize: 13, textAlign: "center", marginTop: 12 },
});
