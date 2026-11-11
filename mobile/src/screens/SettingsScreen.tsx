import React, { useEffect, useState } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { apiGet, clearBaseUrlCache, resolveBaseUrl } from "../api";
import { useAuth } from "../context/AuthContext";
import { setBaseUrl } from "../storage";
import { colors, gradients, radius, shadow } from "../theme";
import {
  Card,
  ErrorText,
  Field,
  PrimaryButton,
  SectionTitle,
} from "../components/ui";
import { FadeInView } from "../components/animated";
import { GlassBackground } from "../components/background";

export default function SettingsScreen() {
  const { user, logout } = useAuth();
  const [serverUrl, setServerUrl] = useState("");
  const [urlDraft, setUrlDraft] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    resolveBaseUrl().then((url) => {
      setServerUrl(url);
      setUrlDraft(url);
    });
  }, []);

  const save = async () => {
    const trimmed = urlDraft.trim();
    if (!/^https?:\/\//.test(trimmed)) {
      setError("Server address must start with http:// or https://");
      return;
    }
    await setBaseUrl(trimmed);
    clearBaseUrlCache();
    setServerUrl(trimmed);
    setError("");
    setMessage("Server address saved.");
  };

  const testConnection = async () => {
    setTesting(true);
    setMessage("");
    setError("");
    try {
      const stats = await apiGet<{ farmers: number; predictions: number; districts: number }>(
        "/api/public/stats"
      );
      setMessage(
        `Connected! ${stats.farmers} farmers, ${stats.predictions} predictions served.`
      );
    } catch {
      setError(
        "Connection failed. Make sure the Flask server is running on the same Wi-Fi and Windows Firewall allows port 5000."
      );
    } finally {
      setTesting(false);
    }
  };

  const statusLabel =
    user?.role === "admin" ? "Admin" : user?.is_approved ? "Approved" : "Pending";
  const statusColor =
    user?.role === "admin" ? colors.primaryDark : user?.is_approved ? "#166534" : "#854d0e";
  const statusBg =
    user?.role === "admin" ? colors.primaryLight : user?.is_approved ? "#dcfce7" : "#fef9c3";

  return (
    <GlassBackground>
      <SafeAreaView style={styles.safe} edges={["top"]}>
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <FadeInView>
          <LinearGradient colors={gradients.hero} style={styles.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
            <Text style={styles.heroEmoji}>⚙️</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>Settings</Text>
              <Text style={styles.subtitle}>Connection and account</Text>
            </View>
          </LinearGradient>
        </FadeInView>

        <FadeInView delay={100}>
          <SectionTitle title="Server Connection" />
        </FadeInView>
        <FadeInView delay={140}>
          <Card>
            <View style={styles.hintRow}>
              <View style={styles.hintIcon}>
                <Ionicons name="wifi" size={15} color={colors.primary} />
              </View>
              <Text style={styles.hint}>
                The phone and the Flask server computer must be on the same Wi-Fi network.
              </Text>
            </View>
            <Field
              label="Server address"
              value={urlDraft}
              onChangeText={setUrlDraft}
              placeholder="http://192.168.1.25:5000"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <View style={styles.btnRow}>
              <PrimaryButton title="Save" onPress={save} style={{ flex: 1 }} />
              <PrimaryButton
                title={testing ? "Testing..." : "Test Connection"}
                onPress={testConnection}
                loading={testing}
                style={{ flex: 1 }}
              />
            </View>
            {message ? (
              <View style={styles.okBox}>
                <Ionicons name="checkmark-circle" size={16} color="#16a34a" />
                <Text style={styles.okText}>{message}</Text>
              </View>
            ) : null}
            <ErrorText message={error} />
          </Card>
        </FadeInView>

        <FadeInView delay={180}>
          <SectionTitle title="Account" />
        </FadeInView>
        <FadeInView delay={220}>
          <Card>
            <View style={styles.userRow}>
              <LinearGradient colors={gradients.primary} style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {(user?.full_name || user?.username || "F").charAt(0).toUpperCase()}
                </Text>
              </LinearGradient>
              <View style={{ flex: 1 }}>
                <Text style={styles.userName}>{user?.full_name || user?.username}</Text>
                <Text style={styles.userEmail}>{user?.email}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: statusBg }]}>
                <Text style={[styles.statusText, { color: statusColor }]}>{statusLabel}</Text>
              </View>
            </View>
            {user?.state ? (
              <View style={styles.userMetaRow}>
                <Ionicons name="location" size={13} color={colors.textMuted} />
                <Text style={styles.userMeta}>State: {user.state}</Text>
              </View>
            ) : null}
          </Card>
        </FadeInView>

        <FadeInView delay={260}>
          <PrimaryButton
            title="Logout"
            onPress={logout}
            style={styles.logoutBtn}
          />
        </FadeInView>

        <FadeInView delay={300}>
          <Text style={styles.about}>
            Farm Wise AI Mobile v1.0.0{"\n"}
            Powered by the Farm Wise AI Flask API
          </Text>
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
    gap: 12,
    borderRadius: radius.xl,
    padding: 18,
    marginBottom: 16,
    ...shadow,
  },
  heroEmoji: { fontSize: 40 },
  title: { fontSize: 20, fontWeight: "800", color: colors.white },
  subtitle: { fontSize: 12, color: "#a7f3d0", marginTop: 4 },
  hintRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 },
  hintIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  hint: { flex: 1, fontSize: 13, color: colors.textMuted },
  btnRow: { flexDirection: "row", gap: 10, marginBottom: 12 },
  okBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#dcfce7",
    borderRadius: radius.sm,
    padding: 10,
    marginBottom: 12,
  },
  okText: { color: "#166534", fontSize: 13, flex: 1 },
  userRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  avatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: { color: colors.white, fontSize: 18, fontWeight: "800" },
  userName: { fontSize: 16, fontWeight: "700", color: colors.text },
  userEmail: { fontSize: 13, color: colors.textMuted, marginTop: 2 },
  statusBadge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
  statusText: { fontSize: 12, fontWeight: "700" },
  userMetaRow: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 10 },
  userMeta: { fontSize: 13, color: colors.textMuted },
  logoutBtn: { backgroundColor: colors.danger, marginTop: 4 },
  about: {
    textAlign: "center",
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 20,
    lineHeight: 18,
  },
});
