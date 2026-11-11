import React, { useState } from "react";
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
import { colors, gradients, shadow } from "../theme";
import { Card, ErrorText, Field, PrimaryButton } from "../components/ui";
import { FadeInView } from "../components/animated";
import { GlassBackground } from "../components/background";

export default function RegisterScreen({ navigation }: { navigation: any }) {
  const { register } = useAuth();
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [state, setStateName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !password) {
      setError("Username, email, and password are required");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
        phone: phone.trim() || undefined,
        state: state.trim() || undefined,
      });
    } catch (e: any) {
      setError(e?.message || "Could not reach the server. Check the server address.");
    } finally {
      setLoading(false);
    }
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
            <View style={styles.header}>
              <LinearGradient colors={gradients.primary} style={styles.logoCircle}>
                <Text style={styles.logo}>👨‍🌾</Text>
              </LinearGradient>
              <Text style={styles.title}>Join Farm Wise AI</Text>
              <Text style={styles.subtitle}>
                New accounts may need admin approval before login
              </Text>
            </View>
          </FadeInView>

          <FadeInView delay={120}>
            <Card>
              <Field
                label="Username"
                value={username}
                onChangeText={setUsername}
                placeholder="e.g. ramesh"
                autoCapitalize="none"
                autoCorrect={false}
              />
              <Field
                label="Full name (optional)"
                value={fullName}
                onChangeText={setFullName}
                placeholder="e.g. Ramesh Kumar"
              />
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
                label="Phone (optional)"
                value={phone}
                onChangeText={setPhone}
                placeholder="10-digit mobile number"
                keyboardType="phone-pad"
              />
              <Field
                label="State (optional)"
                value={state}
                onChangeText={setStateName}
                placeholder="e.g. Karnataka"
              />
              <Field
                label="Password"
                value={password}
                onChangeText={setPassword}
                placeholder="Choose a strong password"
                secureTextEntry
              />

              <ErrorText message={error} />

              <PrimaryButton title="Create Account" onPress={handleRegister} loading={loading} />
            </Card>
          </FadeInView>

          <FadeInView delay={220}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.switchText}>
                Already have an account? <Text style={styles.switchLink}>Login</Text>
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
  header: { alignItems: "center", marginBottom: 24 },
  logoCircle: {
    width: 84,
    height: 84,
    borderRadius: 42,
    alignItems: "center",
    justifyContent: "center",
    ...shadow,
  },
  logo: { fontSize: 40 },
  title: { fontSize: 24, fontWeight: "800", color: colors.text, marginTop: 14 },
  subtitle: { fontSize: 13, color: colors.textMuted, marginTop: 4, textAlign: "center" },
  switchText: { textAlign: "center", fontSize: 14, color: colors.textMuted, marginTop: 18 },
  switchLink: { color: colors.primary, fontWeight: "700" },
});
