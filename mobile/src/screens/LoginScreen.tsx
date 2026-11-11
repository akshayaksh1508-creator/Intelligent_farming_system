import React, { useEffect, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "../context/AuthContext";
import { resolveBaseUrl, clearBaseUrlCache } from "../api";
import { setBaseUrl } from "../storage";
import { colors, gradients, radius, shadow } from "../theme";
import { Card, ErrorText, Field, PrimaryButton } from "../components/ui";
import { FadeInView } from "../components/animated";
import { GlassBackground } from "../components/background";

export default function LoginScreen({ navigation }: { navigation: any }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [serverUrl, setServerUrl] = useState("");
  const [editingUrl, setEditingUrl] = useState(false);
  const [urlDraft, setUrlDraft] = useState("");

  useEffect(() => {
    resolveBaseUrl().then(setServerUrl);
  }, []);

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError("Please enter your email and password");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (e: any) {
      setError(e?.message || "Could not reach the server. Check the server address.");
    } finally {
      setLoading(false);
    }
  };

  const saveUrl = async () => {
    const trimmed = urlDraft.trim();
    if (!/^https?:\/\//.test(trimmed)) {
      setError("Server address must start with http:// or https://");
      return;
    }
    await setBaseUrl(trimmed);
    clearBaseUrlCache();
    setServerUrl(trimmed);
    setEditingUrl(false);
    setError("");
  };

  return (
    <GlassBackground>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <FadeInView distance={26}>
            <View style={styles.logoWrap}>
              <LinearGradient colors={gradients.primary} style={styles.logoCircle}>
                <Text style={styles.logo}>🌾</Text>
              </LinearGradient>
              <Text style={styles.title}>Farm Wise AI</Text>
              <Text style={styles.subtitle}>Smart farming for every farmer</Text>
            </View>
          </FadeInView>

          <FadeInView delay={120}>
            <Card>
              {!editingUrl ? (
                <TouchableOpacity
                  style={styles.serverRow}
                  onPress={() => {
                    setUrlDraft(serverUrl);
                    setEditingUrl(true);
                  }}
                  activeOpacity={0.7}
                >
                  <Text style={styles.serverLabel}>Server</Text>
                  <Text style={styles.serverValue} numberOfLines={1}>
                    {serverUrl || "Detecting..."}
                  </Text>
                  <Text style={styles.serverEdit}>Edit</Text>
                </TouchableOpacity>
              ) : (
                <View>
                  <Field
                    label="Server address (your computer's IP, port 5000)"
                    value={urlDraft}
                    onChangeText={setUrlDraft}
                    placeholder="http://192.168.1.25:5000"
                    autoCapitalize="none"
                    autoCorrect={false}
                    keyboardType="url"
                  />
                  <View style={styles.rowBtns}>
                    <PrimaryButton title="Save" onPress={saveUrl} style={{ flex: 1 }} />
                    <TouchableOpacity
                      style={styles.cancelBtn}
                      onPress={() => setEditingUrl(false)}
                    >
                      <Text style={styles.cancelText}>Cancel</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}

              <Field
                label="Email"
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
              <Field
                label="Password"
                value={password}
                onChangeText={setPassword}
                placeholder="Your password"
                secureTextEntry
              />

              <ErrorText message={error} />

              <PrimaryButton title="Login" onPress={handleLogin} loading={loading} />
            </Card>
          </FadeInView>

          <FadeInView delay={220}>
            <TouchableOpacity onPress={() => navigation.navigate("Register")}>
              <Text style={styles.switchText}>
                New farmer? <Text style={styles.switchLink}>Create an account</Text>
              </Text>
            </TouchableOpacity>
          </FadeInView>
        </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </GlassBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "transparent" },
  container: { flexGrow: 1, justifyContent: "center", padding: 20 },
  logoWrap: { alignItems: "center", marginBottom: 24 },
  logoCircle: {
    width: 92,
    height: 92,
    borderRadius: 46,
    alignItems: "center",
    justifyContent: "center",
    ...shadow,
  },
  logo: { fontSize: 44 },
  title: { fontSize: 28, fontWeight: "800", color: colors.text, marginTop: 14 },
  subtitle: { fontSize: 14, color: colors.textMuted, marginTop: 4 },
  serverRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: "rgba(209,250,229,0.7)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.9)",
    borderRadius: radius.sm,
    padding: 10,
    marginBottom: 14,
  },
  serverLabel: { fontSize: 12, fontWeight: "700", color: colors.primaryDark },
  serverValue: { flex: 1, fontSize: 13, color: colors.primaryDark },
  serverEdit: { fontSize: 13, fontWeight: "700", color: colors.primary },
  rowBtns: { flexDirection: "row", alignItems: "center", gap: 12, marginBottom: 14 },
  cancelBtn: { paddingVertical: 12, paddingHorizontal: 8 },
  cancelText: { color: colors.textMuted, fontSize: 14 },
  switchText: { textAlign: "center", fontSize: 14, color: colors.textMuted, marginTop: 18 },
  switchLink: { color: colors.primary, fontWeight: "700" },
});
