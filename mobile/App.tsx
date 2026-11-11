import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { AuthProvider, useAuth } from "./src/context/AuthContext";
import { colors, gradients } from "./src/theme";
import { PrimaryButton } from "./src/components/ui";
import LoginScreen from "./src/screens/LoginScreen";
import RegisterScreen from "./src/screens/RegisterScreen";
import HomeScreen from "./src/screens/HomeScreen";
import CropScreen from "./src/screens/CropScreen";
import DiseaseScreen from "./src/screens/DiseaseScreen";
import MarketScreen from "./src/screens/MarketScreen";
import SettingsScreen from "./src/screens/SettingsScreen";

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  Main: undefined;
};

export type TabParamList = {
  Home: undefined;
  Crop: undefined;
  Disease: undefined;
  Market: undefined;
  Settings: undefined;
};

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

function TabIcon({
  name,
  focused,
}: {
  name: keyof typeof Ionicons.glyphMap;
  focused: boolean;
}) {
  return (
    <View style={styles.tabIconWrap}>
      {focused ? (
        <LinearGradient
          colors={gradients.primary}
          style={styles.tabBubble}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Ionicons name={name} size={19} color={colors.white} />
        </LinearGradient>
      ) : (
        <Ionicons name={name} size={20} color="#94a3b8" />
      )}
    </View>
  );
}

function Tabs() {
  const insets = useSafeAreaInsets();
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: "#94a3b8",
        tabBarStyle: {
          position: "absolute",
          left: 16,
          right: 16,
          bottom: 12,
          height: 62 + insets.bottom,
          paddingTop: 8,
          paddingBottom: 8 + insets.bottom,
          borderRadius: 32,
          borderTopWidth: 1,
          borderWidth: 1,
          borderColor: "rgba(255,255,255,0.9)",
          backgroundColor: "rgba(255,255,255,0.78)",
          elevation: 16,
          shadowColor: "#047857",
          shadowOpacity: 0.35,
          shadowRadius: 18,
          shadowOffset: { width: 0, height: 8 },
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon name="home" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Crop"
        component={CropScreen}
        options={{
          title: "Crops",
          tabBarIcon: ({ focused }) => <TabIcon name="leaf" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Disease"
        component={DiseaseScreen}
        options={{
          title: "Scan",
          tabBarIcon: ({ focused }) => <TabIcon name="scan" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Market"
        component={MarketScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon name="storefront" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon name="settings" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  );
}

function LoadingScreen({ onRetry }: { onRetry: () => void }) {
  const [showRetry, setShowRetry] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowRetry(true), 9000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <LinearGradient colors={["#ecfdf5", "#d1fae5", "#a7f3d0"]} style={styles.loading}>
      <Text style={styles.loadingEmoji}>🌾</Text>
      <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 16 }} />
      <Text style={styles.loadingText}>Connecting to Farm Wise AI...</Text>
      {showRetry ? (
        <>
          <Text style={styles.loadingHint}>
            Server not responding. Check that Flask is running on your PC and the app's
            server address is your PC's LAN IP.
          </Text>
          <PrimaryButton title="Retry" onPress={onRetry} style={styles.retryBtn} />
        </>
      ) : null}
    </LinearGradient>
  );
}

function Root() {
  const { user, loading, refresh } = useAuth();

  if (loading) {
    return <LoadingScreen onRetry={refresh} />;
  }

  return (
    <NavigationContainer>
      <AuthStack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <AuthStack.Screen name="Main" component={Tabs} options={{ headerShown: false }} />
        ) : (
          <>
            <AuthStack.Screen name="Login" component={LoginScreen} />
            <AuthStack.Screen name="Register" component={RegisterScreen} />
          </>
        )}
      </AuthStack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="dark" />
        <Root />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
  },
  tabIconWrap: {
    width: 38,
    height: 38,
    alignItems: "center",
    justifyContent: "center",
  },
  tabBubble: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#047857",
    shadowOpacity: 0.45,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 4,
  },
  loadingEmoji: { fontSize: 56 },
  loadingText: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.text,
    marginTop: 12,
    textAlign: "center",
  },
  loadingHint: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 18,
    textAlign: "center",
    lineHeight: 19,
  },
  retryBtn: { width: 180, marginTop: 18 },
});
